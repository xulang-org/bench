fn main() {
    let n: i32 = std::env::args().nth(1).and_then(|s| s.parse().ok()).unwrap_or(5_000_000);
    const PI: f64 = std::f64::consts::PI;
    const SOLAR_MASS: f64 = 4.0 * PI * PI;
    const DAYS_PER_YEAR: f64 = 365.24;
    struct Body { x:f64,y:f64,z:f64,vx:f64,vy:f64,vz:f64,mass:f64 }
    let mut sys = [
        Body{x:0.,y:0.,z:0.,vx:0.,vy:0.,vz:0.,mass:SOLAR_MASS},
        Body{x:4.84143144246472090e+00,y:-1.16032004402742839e+00,z:-1.03622044471123109e-01,vx:1.66007664274403694e-03*DAYS_PER_YEAR,vy:7.69901118419740425e-03*DAYS_PER_YEAR,vz:-6.90460016972063023e-05*DAYS_PER_YEAR,mass:9.54791938424326609e-04*SOLAR_MASS},
        Body{x:8.34336671824457987e+00,y:4.12479856412430479e+00,z:-4.03523417114321381e-01,vx:-2.76742510726862411e-03*DAYS_PER_YEAR,vy:4.99852801234917238e-03*DAYS_PER_YEAR,vz:2.30417297573763929e-05*DAYS_PER_YEAR,mass:2.85885980666130812e-04*SOLAR_MASS},
        Body{x:1.28943695621391310e+01,y:-1.51111514016986312e+01,z:-2.23307578892655734e-01,vx:2.96460137564761618e-03*DAYS_PER_YEAR,vy:2.37847173959480950e-03*DAYS_PER_YEAR,vz:-2.96589568540237556e-05*DAYS_PER_YEAR,mass:4.36624404335156298e-05*SOLAR_MASS},
        Body{x:1.53796971148509165e+01,y:-2.59193146099879641e+01,z:1.79258772950371181e-01,vx:2.68067772490389322e-03*DAYS_PER_YEAR,vy:1.62824170038242295e-03*DAYS_PER_YEAR,vz:-9.51592254519715870e-05*DAYS_PER_YEAR,mass:5.15138902046611451e-05*SOLAR_MASS},
    ];
    let (mut px,mut py,mut pz)=(0.,0.,0.);
    for b in &sys { px+=b.vx*b.mass; py+=b.vy*b.mass; pz+=b.vz*b.mass; }
    sys[0].vx=-px/SOLAR_MASS; sys[0].vy=-py/SOLAR_MASS; sys[0].vz=-pz/SOLAR_MASS;
    let energy = |sys: &[Body]| {
        let mut e=0.;
        for i in 0..sys.len() {
            e += 0.5*sys[i].mass*(sys[i].vx*sys[i].vx+sys[i].vy*sys[i].vy+sys[i].vz*sys[i].vz);
            for j in i+1..sys.len() {
                let dx=sys[i].x-sys[j].x; let dy=sys[i].y-sys[j].y; let dz=sys[i].z-sys[j].z;
                e -= sys[i].mass*sys[j].mass/(dx*dx+dy*dy+dz*dz).sqrt();
            }
        }
        e
    };
    println!("{:.9}", energy(&sys));
    for _ in 0..n {
        for i in 0..5 {
            for j in i+1..5 {
                let dx=sys[i].x-sys[j].x; let dy=sys[i].y-sys[j].y; let dz=sys[i].z-sys[j].z;
                let d2=dx*dx+dy*dy+dz*dz; let dist=d2.sqrt(); let mag=0.01/(d2*dist);
                let (mj,mi)=(sys[j].mass,sys[i].mass);
                sys[i].vx-=dx*mj*mag; sys[i].vy-=dy*mj*mag; sys[i].vz-=dz*mj*mag;
                sys[j].vx+=dx*mi*mag; sys[j].vy+=dy*mi*mag; sys[j].vz+=dz*mi*mag;
            }
        }
        for b in &mut sys { b.x+=0.01*b.vx; b.y+=0.01*b.vy; b.z+=0.01*b.vz; }
    }
    println!("{:.9}", energy(&sys));
}
