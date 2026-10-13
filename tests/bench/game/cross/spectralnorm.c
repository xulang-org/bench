#include <stdio.h>
#include <stdlib.h>
#include <math.h>
static int eval_a(int i, int j){ return ((i+j)*(i+j+1)/2 + i + 1); }
static void times(double *v, double *u, int n){
    for(int i=0;i<n;i++){ double s=0; for(int j=0;j<n;j++) s+=u[j]/eval_a(i,j); v[i]=s; }
}
static void timesT(double *v, double *u, int n){
    for(int i=0;i<n;i++){ double s=0; for(int j=0;j<n;j++) s+=u[j]/eval_a(j,i); v[i]=s; }
}
static void AtA(double *v, double *u, int n){
    double *x=calloc(n,sizeof(double)); times(x,u,n); timesT(v,x,n); free(x);
}
int main(int argc,char**argv){
    int n=argc>1?atoi(argv[1]):5500;
    double *u=calloc(n,sizeof(double)), *v=calloc(n,sizeof(double));
    for(int i=0;i<n;i++) u[i]=1;
    for(int k=0;k<10;k++){ AtA(v,u,n); AtA(u,v,n); }
    double vbv=0,vv=0; for(int i=0;i<n;i++){ vbv+=u[i]*v[i]; vv+=v[i]*v[i]; }
    printf("%.9f\n", sqrt(vbv/vv));
    return 0;
}
