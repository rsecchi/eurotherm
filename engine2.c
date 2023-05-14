#include "geometry.h"

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <strings.h>
#include <string.h>

#define MAX_CELLS 30000
#define MAX_GAP 20.0
#define MAX(a,b)  (((a)>(b))?(a):(b))
#define MIN(a,b)  (((a)<(b))?(a):(b))

#define BOTTOM  0x00000001
#define RIGHT   0x00000002
#define FULL    0x00000004
#define WHOLE   0x00000008

#define BTM_LEFT    (BOTTOM)
#define BTM_RIGHT   (BOTTOM | RIGHT)
#define TOP_LEFT    0x00000000
#define TOP_RIGHT   (RIGHT)
#define DIR_MSK     BTM_RIGHT   

#define FULL_WHOLE  (FULL | WHOLE)
#define FULL_TRUNC  (FULL)
#define SEMI_WHOLE  (WHOLE)
#define SEMI_TRUNC  0x00000000
#define HALF_LEFT   0x00000006
#define HALF_RIGHT  0x00000009
#define PACK_MSK    FULL_WHOLE


#define FULL_TOP_LEFT   (FULL | TOP_LEFT)
#define FULL_BTM_LEFT   (FULL | BTM_LEFT)
#define FULL_TOP_RIGHT  (FULL | TOP_RIGHT)
#define FULL_BTM_RIGHT  (FULL | BTM_RIGHT)

//enum {NONE=0, QTR, QTL, SEMIT, QDL, NOID0, HALFLEFT, TQTL,
//  QDR, HALFRIGHT, NOID1, TQTR, SEMIB, TQDR, TQDL, LARGE};

#define LARGE     0x0000000F
#define SEMI_TOP  0x00000003
#define SEMI_BTM  0x0000000C

/* panel types */
int coverFP_W[4][16] = 
{{0, 0, 1, 2, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 4},
 {0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 2, 0, 3, 4},
 {0, 1, 0, 2, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 4},
 {0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 2, 3, 0, 4}};

int costFP_W[4][16] =
{{0, 0, 1, 1, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 1},  
 {0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 2, 1},  
 {0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 1},  
 {0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 2, 0, 1}}; 

int coverFP_T[4][4] =
{{0, 1, 0, 2}, 
 {0, 0, 1, 2}, 
 {0, 1, 0, 2}, 
 {0, 1, 0, 2}};

int costFP_T[4][4] =
{{0, 1, 0, 1},  
 {0, 0, 1, 1},  
 {0, 1, 0, 1},  
 {0, 0, 1, 1}}; 

int coverHP[4][4] =
{{0, 0, 1, 2},  
 {0, 0, 1, 2},  
 {0, 1, 0, 2},  
 {0, 1, 0, 2}}; 

int costHP[4][4] = 
{{0, 0, 1, 1},  
 {0, 0, 1, 1},  
 {0, 1, 0, 1},  
 {0, 1, 0, 1}}; 


char repr[] = { ' ', '\'', '.' , ':' };

typedef struct {
	double  x,  y;  // coordinates of the bottom-left corner
	int    sx, sy;  // horiz/vert sizes in cm

	// 0==TOP_LEFT, 1=BTM_LEFT, 2=TOP_RIGHT, 2=BTM_RIGTH
	int dir;  
} panel;


typedef struct dorsal {
	int i, j;

	uint32_t flags; 
	uint32_t sig;

	int cover, cost;
	int pcover, pcost;
	int ploc;

	struct dorsal* next;
} dorsal;


dorsal* get_dorsal(dorsal** head, int w)
{

	dorsal* dp = *head;
	(*head) += w;

	/* init dorsal */
	memset(dp, 0, w*sizeof(dorsal));

	return dp;
}


typedef struct {
	
	void* grid; // admissible point grid
	int w, h;

	point orig;
	room* rp;

	/* panels */
	panel* pnls;
	int* idx;

	/* head */
	dorsal* dorsals;
	dorsal* free;

} table;


void init_grid(table* ctx)
{
int i, j, h, w;
double cx=ctx->orig.x, cy=ctx->orig.y;
point q;

	h = ctx->h;
	w = ctx->w;

	int (*qs)[w] = (int(*)[w])(ctx->grid);

	for(j=0; j<h; j++) {
		for(i=0; i<w; i++) {

			/* check fit */
			q = (point) {cx + 50*i, cy + 5*j};
			qs[j][i] = fit(&q, ctx->rp);

		}
	}
}


void print_grid(table* t, int offs)
{
int i, j, w, h;
	
	w = t->w;
	h = t->h;

	int (*tbl)[w] = (int (*)[w])(t->grid);

	printf("w=%d h=%d\n", w, h);

	for(j=0; j<h; j++) {
		printf("[");
		for(i=0; i<w; i++) {
			if (tbl[j][i])
				printf(".");
			else
				printf("X");
		}
		printf("]\n");
	}

}

void reg_pnl(table* ctx, double ox, double oy, int sx, int sy, int dir)
{
panel* pnl;

	pnl = &ctx->pnls[*ctx->idx];
	pnl->dir = dir;
	pnl->x = ox;
	pnl->y = oy;
	pnl->sx = sx;
	pnl->sy = sy;
		
	(*ctx->idx)++;
}


void get_panels(table* ctx, dorsal* dors)
{
dorsal* dp;
double ox, oy, dx;
int flgs, dir;
int sig;

	for(dp = dors; dp!=NULL; dp=dp->next) {

		if (dp->ploc==0) 
			continue;

		flgs = dp->flags;
		dir = flgs & DIR_MSK;
		sig = dp->sig;

		printf("%d (%d) - ", sig, dp->i);

		ox = ctx->orig.x + 50*dp->i - 100;
		oy = ctx->orig.y + 5*dp->j - 60;
		dx = (flgs & RIGHT)?100:0;


		if ((flgs & FULL_WHOLE) == FULL_WHOLE) {
			/* full panel */
			if (sig == LARGE) {
				printf("LARGE @ i=%d\n", dp->i);
				printf("ox=%.2lf\n", ox);
				reg_pnl(ctx, dx+ox, oy, 100, 120, dir&(~RIGHT));
				reg_pnl(ctx, dx+ox+100, oy, 100, 120, dir|RIGHT);
				continue;
			}
			
			if ((sig==SEMI_TOP) && !(dir&BOTTOM)) {
				reg_pnl(ctx, dx+ox, oy+60, 100, 60, TOP_LEFT);
				reg_pnl(ctx, dx+ox+100, oy+60, 100, 60, TOP_RIGHT);
				continue;
			} 

			if ((sig==SEMI_BTM) && (dir&BOTTOM)) {
				reg_pnl(ctx, dx+ox, oy, 100, 60, BTM_LEFT);
				reg_pnl(ctx, dx+ox+100, oy, 100, 60, BTM_RIGHT);
				continue;
			}
			

		}

		if ((flgs & PACK_MSK) == FULL_TRUNC) {
			// panel is truncated 
			if (sig==0x03) {
				printf("TRUNC @ i=%d\n", dp->i);
				reg_pnl(ctx, ox+100, oy, 100, 120, dir);
				continue;
			}

			if (sig==0x01) {
				reg_pnl(ctx, ox+200-dx, oy+60, 100, 60, dir);
				continue;
			}
			if (sig==0x02) {
				reg_pnl(ctx, ox+200-dx, oy, 100, 60, dir);
				continue;
			}
		} 

	}

	printf("\n");
}

void print_list(dorsal* dors)
{
dorsal* d;
	printf("  >> ");
	for(d=dors; d!=NULL; d=d->next) {
		if (d->flags & WHOLE)
			printf("W");
		else
			printf("T");
		printf("[%d]=%d  ",d->i, d->cover);
	}
	printf("\n");
}

dorsal* make_dorsal(int flgs, int j, table* ctx)
{
int i, i2, i4, k, w;
dorsal *d, *best;
uint32_t sigW, sigT;
int costW, coverW, coverT, costT, cW, cT;
int coverB, costB;

	if (j<12)
		return NULL;

	w = ctx->w;
	int (*qs)[w] = (int (*)[w])(ctx->grid);

	d = get_dorsal(&ctx->free, w);
	costB = coverB = 0;
	best = NULL;
	for(k=0; k<w-2; k++)
	{
		i  = (flgs & RIGHT)?(w-1-k-2):k;
		i2 = (flgs & RIGHT)?(w-1-k):(k-2);
		i4 = (flgs & RIGHT)?(w-1-k+2):(k-4);

		if (j==20)
			printf("i=%d i2=%d i4=%d\n", i, i2, i4);

		/* init dorsal */
		d[i].flags = flgs;
		d[i].i = i;
		d[i].j = j;
		d[i].next = NULL;

		/* eval cost full panel */	
		costW = coverW = 0;
		sigW = 0;
		if (k>=2 ) {

			sigW = qs[j][i2]*2 + qs[j][i]
				  +qs[j-12][i2]*4 + qs[j-12][i]*8;
			if (j==20)
				printf("sigW=%d\n", sigW);

			if (k>=4) {
				coverW = d[i4].cover; 
				costW  = d[i4].cost;
			}
			cW = coverFP_W[flgs & DIR_MSK][sigW];
			coverW += coverFP_W[flgs & DIR_MSK][sigW];
			costW  +=  costFP_W[flgs & DIR_MSK][sigW];
		}

		/* eval cost truncated panel */
		sigT = qs[j][i] + 2*qs[j-12][i];
		if (j==20)
			printf("sigT=%d\n\n", sigT);

		costT = coverT = 0;
		if (k>=2) {
			coverT = d[i2].cover; 
			costT  = d[i2].cost;
		}
		cT = coverFP_T[flgs & DIR_MSK][sigT];
		coverT += coverFP_T[flgs & DIR_MSK][sigT];
		costT  +=  costFP_T[flgs & DIR_MSK][sigT];

		if (j==20) {
			printf("i=%d   cW=%d sigW=%d, ",i,  coverW, sigW);
			printf("sigT=%d ", sigT);
			printf("cT=%d\n", coverT);
		}

		// choose best between W and T, update dorsal 
		if ( (coverW>coverT) ||
			 (coverW==coverT && costW<costT) )
		{
			if (j==20)
				printf("   CHOOSE W\n");
			// choose WHOLE 
			d[i].cover = coverW;
			d[i].cost = costW;
			d[i].ploc = cW;
			if (k>=4) d[i].next = &d[i4];
			d[i].sig = sigW;
			d[i].flags |= WHOLE;
		} else {
			if (j==20)
				printf("   CHOOSE T\n");
			// choose TRUNCATED 
			d[i].cover = coverT;
			d[i].cost = costT;
			d[i].ploc = cT;
			if (k>=2) d[i].next = &d[i2];
			d[i].sig = sigT;
		}

		/* update overall cover/cost */
		if ( (d[i].ploc==0 || d[i].cover<coverB) || 
			 (d[i].cover==coverB && d[i].cost>costB))
		{
			if (j==20)
				printf("not update\n");
			d[i].cover = coverB;
			d[i].cost = costB;
			d[i].next = best;
		} else {
			if (j==20)
				printf("update\n");
			coverB = d[i].cover;
			costB = d[i].cost;
			best = &d[i];
		}

		
		if (j==20) {
			printf("coverB=%d costB=%d   d[i].cover=%d d[i].cost=%d\n",	
				coverB, costB, d[i].cover, d[i].cost);
			print_list(best);
			printf("\n\n");
		}
		
	}	

	if (j==20)
		get_panels(ctx, best);	

	return best;

}

void scanline(table* ctx)
{
int j, w, h;

	w = ctx->w;
	h = ctx->h;

	
	printf("SCANLINE %d %d\n", w, h);	

	for(j=0; j<h; j++) {
		/* eval j-th line */
		make_dorsal(FULL_BTM_RIGHT, j, ctx);

	}

}




void grid(room r, panel* c,int* n)
{
int offs;
box bb;
int w, h, size;
table ctx;

	*n = 0; // starts with no panels

	bounding_box(&r.walls, &bb);

	ctx.rp = &r;
	w = ctx.w = ceil((bb.xmax - bb.xmin)/50);
	h = ctx.h = ceil((bb.ymax - bb.ymin - 60)/5);
	ctx.pnls = c;
	ctx.idx = n;

	
	int grid[10][h][w];
	
	size = 10*h*w*sizeof(int);

	ctx.dorsals = (dorsal*)malloc(8*size*sizeof(dorsal));
	ctx.free = ctx.dorsals;

	memset(grid, 0, size);

	/* scan offsets */
	for(offs=0; offs<1; offs++) {
	
		/* update context for offs */
		ctx.grid  = grid[offs];
		ctx.orig = (point){bb.xmin + offs*5, bb.ymin};
		init_grid(&ctx);

		// print_grid(&ctx, offs);

		scanline(&ctx);
	}

	printf("size=%d\n", 8*size);
	free(ctx.dorsals);
}

