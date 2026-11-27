use std::sync::mpsc::{sync_channel, Receiver, SyncSender};
use std::thread;

const MOD_V: i64 = 1000000007;

fn worker(rx: Receiver<i64>, res_tx: SyncSender<i64>) {
    let mut hist = [0i64; 256];
    while let Ok(tid) = rx.recv() {
        if tid < 0 {
            return;
        }
        for b in 0..256 {
            hist[b] = 0;
        }
        let mut rng = (tid + 1) * 1000003 + 98765;
        for _ in 0..131072 {
            rng = (rng * 1103515245 + 12345) & 2147483647;
            let bkt = ((rng >> 8) & 255) as usize;
            let val = 1 + ((rng >> 16) & 1023);
            hist[bkt] += val;
        }
        let mut lh = tid + 1;
        for b in 0..256 {
            lh = (lh * 131 + hist[b]) % MOD_V;
        }
        let _ = res_tx.send(lh * 128 + tid);
    }
}

fn main() {
    const N_WORKERS: usize = 8;
    const N_TASKS: usize = 64;

    let mut job_txs = Vec::with_capacity(N_WORKERS);
    let mut job_rxs = Vec::with_capacity(N_WORKERS);
    for _ in 0..N_WORKERS {
        let (tx, rx) = sync_channel::<i64>(16);
        job_txs.push(tx);
        job_rxs.push(Some(rx));
    }
    let (res_tx, res_rx) = sync_channel::<i64>(64);

    let mut handles = Vec::with_capacity(N_WORKERS);
    for w in 0..N_WORKERS {
        let rx = job_rxs[w].take().unwrap();
        let rtx = res_tx.clone();
        handles.push(thread::spawn(move || worker(rx, rtx)));
    }

    for tid in 0..N_TASKS {
        job_txs[tid & 7].send(tid as i64).unwrap();
    }
    for w in 0..N_WORKERS {
        job_txs[w].send(-1).unwrap();
    }

    let mut slot_hash = [0i64; N_TASKS];
    for _ in 0..N_TASKS {
        let packed = res_rx.recv().unwrap();
        let rtid = (packed & 127) as usize;
        let rlh = packed >> 7;
        slot_hash[rtid] = rlh;
    }

    for h in handles {
        let _ = h.join();
    }

    let mut ck: i64 = 0;
    for tid in 0..N_TASKS {
        ck = (ck * 31 + slot_hash[tid]) % MOD_V;
    }

    println!("{}\n{}", N_TASKS * 131072, ck);
}
