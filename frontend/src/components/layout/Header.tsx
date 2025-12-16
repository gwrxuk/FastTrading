"use client";

import { ConnectButton } from "@rainbow-me/rainbowkit";
import { motion } from "framer-motion";
import Link from "next/link";

export function Header() {
  return (
    <header className="bg-terminal-surface/80 backdrop-blur-xl border-b border-terminal-border sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-3"
          >
            <div className="relative">
              <div className="w-10 h-10 bg-gradient-to-br from-accent-primary to-bull rounded-lg flex items-center justify-center">
                <span className="font-display font-bold text-terminal-bg text-lg">F</span>
              </div>
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-bull rounded-full animate-pulse-slow" />
            </div>
            <div>
              <h1 className="font-display font-bold text-xl gradient-text">
                FastTrading
              </h1>
              <p className="text-xs text-terminal-muted -mt-1">
                High-Performance Trading
              </p>
            </div>
          </motion.div>

          {/* Navigation */}
          <nav className="hidden md:flex items-center gap-6">
            <NavLink href="/" active>
              Trade
            </NavLink>
            <NavLink href="/markets">Markets</NavLink>
            <NavLink href="/portfolio">Portfolio</NavLink>
            <NavLink href="/wallet">Wallet</NavLink>
          </nav>

          {/* Right side - Wallet Connection */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-4"
          >
            {/* Network Status */}
            <div className="hidden sm:flex items-center gap-2 text-sm">
              <div className="w-2 h-2 bg-bull rounded-full animate-pulse" />
              <span className="text-terminal-muted">Live</span>
            </div>

            {/* Connect Wallet */}
            <ConnectButton.Custom>
              {({
                account,
                chain,
                openAccountModal,
                openChainModal,
                openConnectModal,
                mounted,
              }) => {
                const ready = mounted;
                const connected = ready && account && chain;

                return (
                  <div
                    {...(!ready && {
                      "aria-hidden": true,
                      style: {
                        opacity: 0,
                        pointerEvents: "none",
                        userSelect: "none",
                      },
                    })}
                  >
                    {(() => {
                      if (!connected) {
                        return (
                          <button
                            onClick={openConnectModal}
                            className="btn-primary flex items-center gap-2"
                          >
                            <WalletIcon />
                            Connect Wallet
                          </button>
                        );
                      }

                      if (chain.unsupported) {
                        return (
                          <button
                            onClick={openChainModal}
                            className="bg-bear text-white px-4 py-2 rounded-lg font-semibold"
                          >
                            Wrong Network
                          </button>
                        );
                      }

                      return (
                        <div className="flex items-center gap-2">
                          <button
                            onClick={openChainModal}
                            className="flex items-center gap-2 bg-terminal-elevated border border-terminal-border 
                                     px-3 py-2 rounded-lg hover:border-accent-primary/50 transition-colors"
                          >
                            {chain.hasIcon && chain.iconUrl && (
                              <img
                                alt={chain.name ?? "Chain icon"}
                                src={chain.iconUrl}
                                className="w-5 h-5"
                              />
                            )}
                            <span className="text-sm hidden sm:inline">
                              {chain.name}
                            </span>
                          </button>

                          <button
                            onClick={openAccountModal}
                            className="flex items-center gap-2 bg-terminal-elevated border border-terminal-border 
                                     px-3 py-2 rounded-lg hover:border-accent-primary/50 transition-colors"
                          >
                            <div className="w-5 h-5 rounded-full bg-gradient-to-br from-accent-primary to-bull" />
                            <span className="font-mono text-sm">
                              {account.displayName}
                            </span>
                          </button>
                        </div>
                      );
                    })()}
                  </div>
                );
              }}
            </ConnectButton.Custom>
          </motion.div>
        </div>
      </div>
    </header>
  );
}

function NavLink({
  href,
  children,
  active = false,
}: {
  href: string;
  children: React.ReactNode;
  active?: boolean;
}) {
  return (
    <Link
      href={href}
      className={`text-sm font-medium transition-colors hover:text-accent-primary
        ${active ? "text-accent-primary" : "text-terminal-muted"}`}
    >
      {children}
    </Link>
  );
}

function WalletIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21 12V7H5a2 2 0 0 1 0-4h14v4" />
      <path d="M3 5v14a2 2 0 0 0 2 2h16v-5" />
      <path d="M18 12a2 2 0 0 0 0 4h4v-4Z" />
    </svg>
  );
}

