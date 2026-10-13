use std::sync::mpsc::sync_channel;
use std::thread;

fn worker(tx: std::sync::mpsc::SyncSender<i64>, n: i64) {
    let mut i: i64 = 0;
    while i < n {
        tx.send(i).unwrap();
        i += 1;
    }
}

fn main() {
    let (tx, rx) = sync_channel(64);
    thread::spawn(move || {
        worker(tx, 500_000);
    });
    let mut s: i64 = 0;
    let mut i: i64 = 0;
    while i < 500_000 {
        s += rx.recv().unwrap();
        i += 1;
    }
    println!("{}", s);
}
