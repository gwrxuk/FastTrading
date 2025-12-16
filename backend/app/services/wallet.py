"""
Wallet Service
Web3 wallet management and blockchain interaction
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List
from uuid import UUID, uuid4
import secrets

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct

from app.models.wallet import Wallet, Transaction, WalletType, TransactionType, TransactionStatus
from app.schemas.wallet import (
    WalletCreate, WalletResponse, TransactionCreate,
    SignMessageRequest, SignMessageResponse, GasEstimate, WalletBalance
)
from app.config import settings


class WalletService:
    """
    Wallet service providing:
    - Wallet creation and binding
    - Signature verification
    - Balance tracking
    - Transaction management
    - Gas estimation
    """
    
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.ETH_NODE_URL))
        self._pending_signatures: dict[str, dict] = {}  # nonce -> {address, expires_at}
    
    def generate_sign_message(self, address: str) -> SignMessageResponse:
        """
        Generate a unique message for wallet signature verification
        """
        nonce = secrets.token_hex(16)
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        message = (
            f"Welcome to FastTrading!\n\n"
            f"Sign this message to verify wallet ownership.\n\n"
            f"Wallet: {address}\n"
            f"Nonce: {nonce}\n\n"
            f"This signature will NOT trigger a blockchain transaction or cost any gas."
        )
        
        # Store for verification
        self._pending_signatures[nonce] = {
            "address": address.lower(),
            "expires_at": expires_at,
            "message": message
        }
        
        return SignMessageResponse(
            message=message,
            nonce=nonce,
            expires_at=expires_at
        )
    
    def verify_signature(
        self,
        address: str,
        message: str,
        signature: str,
        nonce: Optional[str] = None
    ) -> bool:
        """
        Verify wallet signature
        Uses EIP-191 personal_sign standard
        """
        try:
            # Verify nonce if provided
            if nonce:
                pending = self._pending_signatures.get(nonce)
                if not pending:
                    return False
                if pending["expires_at"] < datetime.utcnow():
                    del self._pending_signatures[nonce]
                    return False
                if pending["address"] != address.lower():
                    return False
                # Clean up used nonce
                del self._pending_signatures[nonce]
            
            # Recover address from signature
            message_hash = encode_defunct(text=message)
            recovered = Account.recover_message(message_hash, signature=signature)
            
            return recovered.lower() == address.lower()
        except Exception as e:
            print(f"Signature verification failed: {e}")
            return False
    
    async def bind_wallet(
        self,
        db: AsyncSession,
        user_id: UUID,
        wallet_create: WalletCreate
    ) -> Optional[Wallet]:
        """
        Bind an external wallet to user account
        Verifies ownership via signature
        """
        # Verify signature
        if not self.verify_signature(
            wallet_create.address,
            wallet_create.message,
            wallet_create.signature
        ):
            return None
        
        # Check if wallet already exists
        result = await db.execute(
            select(Wallet).where(Wallet.address == wallet_create.address.lower())
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            return None  # Wallet already bound
        
        # Create wallet record
        wallet = Wallet(
            user_id=user_id,
            wallet_type=WalletType.USER,
            address=wallet_create.address.lower(),
            chain=wallet_create.chain,
            currency=wallet_create.currency,
            balance=Decimal(0),
            locked_balance=Decimal(0),
            is_verified="verified"
        )
        
        db.add(wallet)
        await db.flush()
        await db.refresh(wallet)
        
        # Fetch initial balance
        await self._sync_wallet_balance(wallet)
        
        return wallet
    
    async def _sync_wallet_balance(self, wallet: Wallet) -> None:
        """
        Sync wallet balance from blockchain
        """
        try:
            if wallet.currency == "ETH":
                balance_wei = self.w3.eth.get_balance(
                    Web3.to_checksum_address(wallet.address)
                )
                wallet.balance = Decimal(str(balance_wei)) / Decimal(10 ** 18)
        except Exception as e:
            print(f"Balance sync failed: {e}")
    
    async def get_user_wallets(
        self,
        db: AsyncSession,
        user_id: UUID
    ) -> List[Wallet]:
        """Get all wallets for user"""
        result = await db.execute(
            select(Wallet).where(Wallet.user_id == user_id)
        )
        return result.scalars().all()
    
    async def get_wallet_balances(
        self,
        db: AsyncSession,
        user_id: UUID
    ) -> List[WalletBalance]:
        """Get aggregated balances for user"""
        wallets = await self.get_user_wallets(db, user_id)
        
        return [
            WalletBalance(
                currency=w.currency,
                available=w.balance - w.locked_balance,
                locked=w.locked_balance,
                total=w.balance
            )
            for w in wallets
        ]
    
    async def estimate_gas(
        self,
        to_address: str,
        amount: Decimal,
        currency: str = "ETH"
    ) -> GasEstimate:
        """
        Estimate gas for transaction
        """
        try:
            gas_price = self.w3.eth.gas_price
            gas_limit = 21000  # Standard ETH transfer
            
            if currency != "ETH":
                gas_limit = 65000  # ERC20 transfer
            
            fee_wei = gas_price * gas_limit
            fee_eth = Decimal(str(fee_wei)) / Decimal(10 ** 18)
            
            # Estimate USD (using cached ETH price)
            eth_usd = Decimal("2250")  # Would come from market service
            fee_usd = fee_eth * eth_usd
            
            return GasEstimate(
                gas_limit=gas_limit,
                gas_price_gwei=Decimal(str(gas_price)) / Decimal(10 ** 9),
                estimated_fee_eth=fee_eth,
                estimated_fee_usd=fee_usd
            )
        except Exception:
            # Fallback values
            return GasEstimate(
                gas_limit=21000,
                gas_price_gwei=Decimal("30"),
                estimated_fee_eth=Decimal("0.00063"),
                estimated_fee_usd=Decimal("1.42")
            )
    
    async def create_withdrawal(
        self,
        db: AsyncSession,
        user_id: UUID,
        wallet_id: UUID,
        tx_create: TransactionCreate
    ) -> Optional[Transaction]:
        """
        Create withdrawal transaction
        """
        # Get wallet
        result = await db.execute(
            select(Wallet).where(
                Wallet.id == wallet_id,
                Wallet.user_id == user_id
            )
        )
        wallet = result.scalar_one_or_none()
        
        if not wallet:
            return None
        
        # Check balance
        available = wallet.balance - wallet.locked_balance
        if tx_create.amount > available:
            return None
        
        # Lock funds
        wallet.locked_balance += tx_create.amount
        
        # Create transaction record
        tx = Transaction(
            wallet_id=wallet_id,
            user_id=user_id,
            tx_type=TransactionType.WITHDRAWAL,
            status=TransactionStatus.PENDING,
            from_address=wallet.address,
            to_address=tx_create.to_address.lower(),
            currency=tx_create.currency,
            amount=tx_create.amount
        )
        
        db.add(tx)
        await db.flush()
        await db.refresh(tx)
        
        return tx
    
    async def get_transactions(
        self,
        db: AsyncSession,
        user_id: UUID,
        limit: int = 50
    ) -> List[Transaction]:
        """Get user's transactions"""
        result = await db.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    def is_valid_address(self, address: str) -> bool:
        """Validate Ethereum address format"""
        try:
            return Web3.is_address(address)
        except Exception:
            return False


# Singleton instance
wallet_service = WalletService()

