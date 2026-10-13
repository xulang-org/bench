/* Benchmarks Game n-body — single-thread */
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define NB 5
static const double PI = 3.141592653589793;
static const double SOLAR_MASS = 4.0 * PI * PI;
static const double DAYS_PER_YEAR = 365.24;

typedef struct { double x,y,z,vx,vy,vz,mass; } Body;

static Body sys[NB];

static void offset_momentum(void) {
    double px=0,py=0,pz=0;
    for (int i=0;i<NB;i++){ px+=sys[i].vx*sys[i].mass; py+=sys[i].vy*sys[i].mass; pz+=sys[i].vz*sys[i].mass; }
    sys[0].vx=-px/SOLAR_MASS; sys[0].vy=-py/SOLAR_MASS; sys[0].vz=-pz/SOLAR_MASS;
}
static double energy(void) {
    double e=0;
    for (int i=0;i<NB;i++){
        e+=0.5*sys[i].mass*(sys[i].vx*sys[i].vx+sys[i].vy*sys[i].vy+sys[i].vz*sys[i].vz);
        for (int j=i+1;j<NB;j++){
            double dx=sys[i].x-sys[j].x, dy=sys[i].y-sys[j].y, dz=sys[i].z-sys[j].z;
            e-=sys[i].mass*sys[j].mass/sqrt(dx*dx+dy*dy+dz*dz);
        }
    }
    return e;
}
static void advance(double dt) {
    for (int i=0;i<NB;i++) for (int j=i+1;j<NB;j++){
        double dx=sys[i].x-sys[j].x, dy=sys[i].y-sys[j].y, dz=sys[i].z-sys[j].z;
        double d2=dx*dx+dy*dy+dz*dz, dist=sqrt(d2), mag=dt/(d2*dist);
        sys[i].vx-=dx*sys[j].mass*mag; sys[i].vy-=dy*sys[j].mass*mag; sys[i].vz-=dz*sys[j].mass*mag;
        sys[j].vx+=dx*sys[i].mass*mag; sys[j].vy+=dy*sys[i].mass*mag; sys[j].vz+=dz*sys[i].mass*mag;
    }
    for (int i=0;i<NB;i++){ sys[i].x+=dt*sys[i].vx; sys[i].y+=dt*sys[i].vy; sys[i].z+=dt*sys[i].vz; }
}
int main(int argc, char **argv) {
    int n = argc>1 ? atoi(argv[1]) : 5000000;
    sys[0]=(Body){0,0,0,0,0,0,SOLAR_MASS};
    sys[1]=(Body){4.84143144246472090e+00,-1.16032004402742839e+00,-1.03622044471123109e-01,
        1.66007664274403694e-03*DAYS_PER_YEAR,7.69901118419740425e-03*DAYS_PER_YEAR,-6.90460016972063023e-05*DAYS_PER_YEAR,
        9.54791938424326609e-04*SOLAR_MASS};
    sys[2]=(Body){8.34336671824457987e+00,4.12479856412430479e+00,-4.03523417114321381e-01,
        -2.76742510726862411e-03*DAYS_PER_YEAR,4.99852801234917238e-03*DAYS_PER_YEAR,2.30417297573763929e-05*DAYS_PER_YEAR,
        2.85885980666130812e-04*SOLAR_MASS};
    sys[3]=(Body){1.28943695621391310e+01,-1.51111514016986312e+01,-2.23307578892655734e-01,
        2.96460137564761618e-03*DAYS_PER_YEAR,2.37847173959480950e-03*DAYS_PER_YEAR,-2.96589568540237556e-05*DAYS_PER_YEAR,
        4.36624404335156298e-05*SOLAR_MASS};
    sys[4]=(Body){1.53796971148509165e+01,-2.59193146099879641e+01,1.79258772950371181e-01,
        2.68067772490389322e-03*DAYS_PER_YEAR,1.62824170038242295e-03*DAYS_PER_YEAR,-9.51592254519715870e-05*DAYS_PER_YEAR,
        5.15138902046611451e-05*SOLAR_MASS};
    offset_momentum();
    printf("%.9f\n", energy());
    for (int i=0;i<n;i++) advance(0.01);
    printf("%.9f\n", energy());
    return 0;
}
