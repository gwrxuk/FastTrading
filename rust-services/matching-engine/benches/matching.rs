//! Benchmarks for the matching engine
//!
//! Run with: cargo bench --package matching-engine

use criterion::{black_box, criterion_group, criterion_main, Criterion, Throughput};
use rust_decimal::Decimal;
use uuid::Uuid;

use common::{Order, OrderStatus, OrderType, Side, Symbol, TimeInForce};
use matching_engine::orderbook::OrderBook;

fn create_order(side: Side, price: Decimal, quantity: Decimal) -> Order {
    Order {
        id: Uuid::new_v4(),
        client_order_id: Uuid::new_v4().to_string(),
        user_id: Uuid::new_v4(),
        symbol: Symbol::new("BTC", "USDT"),
        side,
        order_type: OrderType::Limit,
        time_in_force: TimeInForce::GTC,
        status: OrderStatus::Pending,
        price: Some(price),
        stop_price: None,
        quantity,
        filled_quantity: Decimal::ZERO,
        remaining_quantity: quantity,
        avg_fill_price: None,
        sequence: 0,
        created_at: chrono::Utc::now(),
        updated_at: chrono::Utc::now(),
    }
}

fn bench_order_insertion(c: &mut Criterion) {
    let mut group = c.benchmark_group("order_insertion");
    group.throughput(Throughput::Elements(1));

    group.bench_function("insert_limit_order", |b| {
        let book = OrderBook::new(Symbol::new("BTC", "USDT"));
        let mut price = Decimal::new(50000, 0);

        b.iter(|| {
            let order = create_order(Side::Buy, price, Decimal::new(1, 0));
            black_box(book.process_order(order));
            price += Decimal::new(1, 0);
        });
    });

    group.finish();
}

fn bench_order_matching(c: &mut Criterion) {
    let mut group = c.benchmark_group("order_matching");
    group.throughput(Throughput::Elements(1));

    group.bench_function("match_single_order", |b| {
        b.iter_batched(
            || {
                let book = OrderBook::new(Symbol::new("BTC", "USDT"));
                // Pre-populate with sell orders
                for i in 0..100 {
                    let price = Decimal::new(50000 + i, 0);
                    let order = create_order(Side::Sell, price, Decimal::new(1, 0));
                    book.process_order(order);
                }
                book
            },
            |book| {
                let buy = create_order(Side::Buy, Decimal::new(50050, 0), Decimal::new(1, 0));
                black_box(book.process_order(buy));
            },
            criterion::BatchSize::SmallInput,
        );
    });

    group.finish();
}

fn bench_order_cancellation(c: &mut Criterion) {
    let mut group = c.benchmark_group("order_cancellation");
    group.throughput(Throughput::Elements(1));

    group.bench_function("cancel_order", |b| {
        b.iter_batched(
            || {
                let book = OrderBook::new(Symbol::new("BTC", "USDT"));
                let order = create_order(Side::Buy, Decimal::new(50000, 0), Decimal::new(1, 0));
                let order_id = order.id;
                book.process_order(order);
                (book, order_id)
            },
            |(book, order_id)| {
                black_box(book.cancel_order(order_id));
            },
            criterion::BatchSize::SmallInput,
        );
    });

    group.finish();
}

fn bench_depth_retrieval(c: &mut Criterion) {
    let mut group = c.benchmark_group("depth_retrieval");

    let book = OrderBook::new(Symbol::new("BTC", "USDT"));
    // Pre-populate with orders
    for i in 0..1000 {
        let buy_price = Decimal::new(49000 + i, 0);
        let sell_price = Decimal::new(51000 + i, 0);
        book.process_order(create_order(Side::Buy, buy_price, Decimal::new(1, 0)));
        book.process_order(create_order(Side::Sell, sell_price, Decimal::new(1, 0)));
    }

    group.bench_function("get_depth_20", |b| {
        b.iter(|| {
            black_box(book.get_depth(20));
        });
    });

    group.bench_function("get_bbo", |b| {
        b.iter(|| {
            black_box(book.get_bbo());
        });
    });

    group.finish();
}

criterion_group!(
    benches,
    bench_order_insertion,
    bench_order_matching,
    bench_order_cancellation,
    bench_depth_retrieval,
);
criterion_main!(benches);
