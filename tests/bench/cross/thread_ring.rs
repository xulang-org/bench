use std::sync::mpsc::{sync_channel, Receiver, SyncSender};
use std::thread;

fn node(id: i64, rx: Receiver<i64>, tx: SyncSender<i64>, done: SyncSender<i64>) {
    loop {
        match rx.recv() {
            Ok(v) => {
                if v < 0 {
                    let _ = tx.send(-1);
                    return;
                }
                if v == 0 {
                    let _ = done.send(id);
                    let _ = tx.send(-1);
                    return;
                }
                if tx.send(v - 1).is_err() {
                    return;
                }
            }
            Err(_) => return,
        }
    }
}

fn main() {
    let n = 503usize;
    let mut txs = Vec::with_capacity(n);
    let mut rxs = Vec::with_capacity(n);
    for _ in 0..n {
        let (tx, rx) = sync_channel::<i64>(1);
        txs.push(tx);
        rxs.push(Some(rx));
    }
    let (done_tx, done_rx) = sync_channel::<i64>(1);

    let mut handles = Vec::with_capacity(n);
    for i in 0..n {
        let nxt = (i + 1) % n;
        let rx = rxs[i].take().unwrap();
        let tx = txs[nxt].clone();
        let dtx = done_tx.clone();
        let h = thread::Builder::new()
            .stack_size(128 * 1024)
            .spawn(move || node((i + 1) as i64, rx, tx, dtx))
            .unwrap();
        handles.push(h);
    }

    txs[0].send(100_000).unwrap();
    let winner = done_rx.recv().unwrap();
    for h in handles {
        let _ = h.join();
    }
    println!("{}", winner);
}
