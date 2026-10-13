fn qsort(a: &mut [i64], low: isize, high: isize) {
    if low >= high {
        return;
    }
    let pivot = a[((low + high) / 2) as usize];
    let mut i = low;
    let mut j = high;
    while i <= j {
        while a[i as usize] < pivot {
            i += 1;
        }
        while a[j as usize] > pivot {
            j -= 1;
        }
        if i <= j {
            a.swap(i as usize, j as usize);
            i += 1;
            j -= 1;
        }
    }
    if low < j {
        qsort(a, low, j);
    }
    if i < high {
        qsort(a, i, high);
    }
}

fn main() {
    let mut checksum: i64 = 0;
    let mut arr = vec![0i64; 100000];

    for round in 0..5 {
        let mut seed: i64 = 123456789 + (round as i64) * 1013904223;
        for k in 0..100000 {
            seed = (seed * 1664525 + 1013904223) % 2147483647;
            arr[k] = seed;
        }
        qsort(&mut arr, 0, 99999);
        for i in 0..100000 {
            checksum = (checksum * 31 + arr[i]) % 1000000007;
        }
    }

    println!("{}", checksum);
}
