#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <strings.h>
#define EPS 1e-6

#define NO_CROSS 0
#define CROSS    1
#define TOUCH    2
#define MAX_CELLS 30000
#define MAX(a,b)  (((a)>(b))?(a):(b))
#define MIN(a,b)  (((a)<(b))?(a):(b))
#define MAX_VALS 1000
#define MAX_ITER 1000000

enum mode {INSIDE, OUTSIDE, INTERSECT};

typedef struct {
	double x, y;	
} point;

typedef struct {
	point* poly;
	int len;
} polygon;

typedef struct {
	polygon walls;
	polygon* obstacles;
	int obs_num;
} room;

typedef struct {
	double xmin, xmax;
	double ymin, ymax;
} box;

typedef struct {
	int row, col;
	double x, y;
} cell;

typedef struct {
	int i,j;
	int count;
	int score;
} str;

typedef struct {
	str* sp;
	int size;
	int best_align;
	void* tbl;
} block;

struct {
	void* tbl;
	int* score;
	int w, h;
} table;

void* tblb;
int iter;

/* check if p is inside poly */
int inside(point *q, polygon* pgon)
{
int i, count = 0;
point *p = pgon->poly;
double ax, ay, bx, by, dd;
double xp = q->x;
double yp = q->y;

	for(i=0; i<pgon->len-1; i++)
	{
		ax = p[i].x;
		ay = p[i].y;
		bx = p[i+1].x;
		by = p[i+1].y;

		if ((ay>yp && by>yp) || (ay<yp && by<yp))
			continue;

		/* sidestep cases of alignment */
		if (ay==yp || by==yp) {
			yp += EPS;
			return inside(&(point){xp, yp}, pgon);
		}

		dd = (bx - ax)*(yp - ay) - (xp - ax)*(by - ay);
		if ((dd>0 && by>ay) || (dd<0 && by<ay))
			count++;
	}
	return (count % 2) == 1;
}


int cross(point* a, point* b)
{
	double dd, dt, ds;
	double dax, day, dbx, dby, d0x, d0y;

	/* differentials */
	dax = a[1].x - a[0].x;
	day = a[1].y - a[0].y;
	dbx = b[1].x - b[0].x;
	dby = b[1].y - b[0].y;
	d0x = a[0].x - b[0].x;
	d0y = a[0].y - b[0].y;

	/* determinants */
	dd = -dax * dby + dbx * day;
	dt =  d0x * dby - dbx * d0y;
	ds = -dax * d0y + d0x * day;


	//printf("dd=%lf ds=%lf dt=%lf\n", dd, ds, dt);

	if ( ((ds==0 || ds==dd) && (0<=dt && dt<=dd)) ||
		 ((dt==0 || dt==dd) && (0<=ds && ds<=dd)))
		return TOUCH;

	if (dd==0)
		return NO_CROSS;

	if (dd<0)
		return ((dd<ds) && (ds<0) && (dd<dt) && (dt<0))?CROSS:NO_CROSS;
	else
		return ((0<ds) && (ds<dd) && (0<dt) && (dt<dd))?CROSS:NO_CROSS;
}



int check_box(int mode, box* bb, polygon* pgon)
{
double x, y;
point centre;
point vbox[5];
int i,j,res;

	centre = (point){(bb->xmin+bb->xmax)/2, 
                     (bb->ymin+bb->ymax)/2};

	res = inside(&centre, pgon);

	if ((mode==INSIDE && !res) ||
		(mode==OUTSIDE && res))
		return 0;

	vbox[0] = (point){bb->xmin+2*EPS, bb->ymin};
	vbox[1] = (point){bb->xmin+2*EPS, bb->ymax};
	vbox[2] = (point){bb->xmax, bb->ymax};
	vbox[3] = (point){bb->xmax, bb->ymin};
	vbox[4] = vbox[0];

	for(i=0; i<pgon->len-1; i++) {
		x = pgon->poly[i].x;
		y = pgon->poly[i].y;
		if (bb->xmin<x && x<bb->xmax && 
			bb->ymin<y && y<bb->ymax)
			return 0; 

		for(j=0; j<4; j++) {

			res = cross(&pgon->poly[i], &vbox[j]);

			if (res == CROSS)
				return mode==INTERSECT;
		}
	}

	return mode!=INTERSECT;
} 


void bounding_box(polygon* pgon, box* bb)
{
double x,y;
double xmin, xmax, ymin, ymax;
int i;

	xmin = xmax = pgon->poly[0].x;
	ymin = ymax = pgon->poly[0].y;

	for(i=0; i<pgon->len-1; i++) {
		x = pgon->poly[i].x;
		y = pgon->poly[i].y;

		if (x<xmin)	xmin = x;
		if (x>xmax) xmax = x;
		if (y<ymin) ymin = y;
		if (y>ymax) ymax = y;
	}

	bb->xmin = xmin;
	bb->xmax = xmax;
	bb->ymin = ymin;
	bb->ymax = ymax;
}


double hdist(point* q, polygon* pgon)
{
int i;
point *p = pgon->poly;
double ax, ay, bx, by;
double xp = q->x;
double yp = q->y;
double d, dmin;

	dmin = INFINITY;

	for(i=0; i<pgon->len-1; i++)
	{
		ax = p[i].x;
		ay = p[i].y;
		bx = p[i+1].x;
		by = p[i+1].y;

		if ((ay>yp && by>yp) || (ay<yp && by<yp))
			continue;

		if (ay==by) {
			/* point aligned with line */
			d = MIN(fabs(bx-xp), fabs(ax - xp));
		} else {
			/* denom cannot be zero */
			d = fabs(ax-xp+(yp-ay)*(bx-ax)/(by-ay));
		}

		dmin = MIN(dmin, d);
	}
	return dmin;
}

int fit(point* p, room* r)
{
int i;
box panel;

	/* build box */			
	panel.xmin = p->x;
	panel.xmax = p->x+50;
	panel.ymin = p->y;
	panel.ymax = p->y+60;

	/* check if inside room */
	if (!check_box(INSIDE, &panel, &r->walls))
		return 0;

	/* check if outside obstacles */
	for(i=0; i<r->obs_num; i++)
		if (!check_box(OUTSIDE, &panel, &(r->obstacles[i])))
			return 0;

	return 1;
}


int gap_is_okay(point *q, room *r)
{
int i;

	for(i=0; i<4; i++)
		if (hdist(&q[i], &(r->walls))<20.0)
			return 0;

	return 1;
}

void fill_matrix(int offs, point p, room* r, void* mat, int w, int h)
{
int i, j;
double cx=p.x+offs*5, cy=p.y;
point q[4];

	int (*qs)[h][w] = (int(*)[h][w]) mat;

	for(j=0; j<h; j++) {
		for(i=0; i<w; i++) {

			(*qs)[j][i] = 0;
			
			/* disregard too close gaps */
			q[0] = (point) {cx + 50*i, cy + 5*j};
			q[1] = (point) {cx + 50*i +50, cy + 5*j};
			q[2] = (point) {cx + 50*i, cy + 5*j + 60};
			q[3] = (point) {cx + 50*i +50, cy + 5*j + 60};

			if (!gap_is_okay(q, r))
				continue;	

			/* check fit */
			(*qs)[j][i] = fit(q, r);

		}
	}

}

void print_table()
{
int i, j, w, h;
int* score;
	
	w = table.w;
	h = table.h;

	typedef int (*table_p)[w];
	table_p tbl = (table_p)(table.tbl);	
	score = table.score;

	printf("w=%d h=%d\n", w, h);

	for(j=0; j<h; j++) {
		printf("[");
		for(i=0; i<w; i++)
			if (tbl[j][i])
				printf(".");
			else
				printf("X");
		printf("] score[%d]=%d\n", j, score[j]);
	}
}

void print_block(block *blk)
{
int i, j, w;
int* score;
int top, btm;

	top = blk->sp[0].j;
	btm = blk->sp[blk->size-1].j;

	w = table.w;

	typedef int (*table_p)[table.w];
	table_p tbl = (table_p)(table.tbl);	
	score = table.score;


	for(j=top; j>=btm; j-=12) {
		printf("[");
		for(i=0; i<w; i++) {
			if (tbl[j][i]==1)
				printf(".");
			
			if (tbl[j][i]==0)
				printf("X");

			if (tbl[j][i]==2)
				printf("[");
			
			if (tbl[j][i]==3)
				printf("]");
		}
		printf("] score[%d]=%d\n", j, score[j]);
	}
	
}

void print_best_bl(block *blk)
{
int i, j, w;
int top, btm;

	top = blk->sp[0].j;
	btm = blk->sp[blk->size-1].j;

	w = table.w;

	typedef int (*table_p)[table.w];
	table_p tbl = (table_p)(blk->tbl);	

	for(j=top; j>=btm; j-=12) {
		printf("[");
		for(i=0; i<w; i++) {
			if (tbl[j][i]==1)
				printf(".");
			
			if (tbl[j][i]==0)
				printf("X");

			if (tbl[j][i]==2)
				printf("[");
			
			if (tbl[j][i]==3)
				printf("]");
		}
		printf("]\n");
	}
	
}

int count_row(int* row, int w, str** p, int j)
{
str *sp;
int i, count, line;

	line = 0;
	for(i=0; i<w; i++) {

		count = 0;
		while((i<w) && row[i]) {
			count++;
			i++;
		}
				
		if (count>0) {
			line += count/2;
			if (p) {
				sp = *p;
				sp->i = i;
				sp->j = j;
				sp->count = count;
				sp->score = line;
				(*p)++;
			}
		}
	}
			
	return line;
}

int align_score(block *blk)
{
int i, j, w;
int count;
int top, btm;
int hscore, vscore;

	top = blk->sp[0].j;
	btm = blk->sp[blk->size-1].j;

	if (top==btm)
		return 0;

	w = table.w;

	typedef int (*table_p)[w];
	table_p tbl = (table_p)(table.tbl);	

	hscore = 0;
	/* count potential+cumulated horizontal joins */
	for(j=top-12; j>=btm; j-=12) {
		count = 0;
		for(i=0; i<w; i++) {

			if (tbl[j][i]==1 && tbl[j+12][i]!=0) {
				count++;
				continue;
			}
			hscore += count/2;
			count = 0;

			if ( (tbl[j][i]==2 && tbl[j+12][i]==2) ||
			     (tbl[j][i]==2 && tbl[j+12][i]==1 &&
				 tbl[j+12][i]==1) )
			{
				hscore++;
				i++;	
			}
		}
		hscore += count/2;
	}

	/* count potential+cumulated vertical joins */
	vscore = 0;
	for(j=top; j>=btm; j-=12) {
		count = 0;
		for(i=0; i<w; i++) {
			if (tbl[j][i]==1) {
				count++;
				continue;
			}
			if (count>2)
				vscore += (count/2)-1;
			count = 0;

			if (i<w-1 && tbl[j][i]==3 
					  && tbl[j][i+1]==2)
				vscore++;

		}
		if (count>2)
			vscore += (count/2)-1;
	}
	
	return hscore + vscore;
}

void align_cells(block *blk, int lvl)
{
int i, j, k, w, s;
int ic, jc, sc;
int top, btm;
int pnls;
int best_sofar, hope_for;
str* sp;

	iter++;
	if (iter>MAX_ITER)
		return;

	printf("LVL=%d\n", lvl);
	print_block(blk);
	printf("align_score=%d\n", align_score(blk));

	w = table.w;
	typedef int (*table_p)[w];
	table_p tbl = (table_p)(table.tbl);	
	s = blk->size;

	sp = blk->sp;
	top = sp[0].j;
	btm = sp[s-1].j;

	/* terminal case */
	if (lvl==blk->size) {
		printf("reach terminal\n");
		blk->best_align = align_score(blk);
		printf("total alignment: %d\n", blk->best_align);

		/* copy best solution */
		table_p tblb = (table_p)(blk->tbl);	
		for(j=top; j>=btm; j-=12) 
			for(i=0; i<w; i++) 
				tblb[j][i] = tbl[j][i];

		return;
	}


	sc = sp[lvl].count;
	if (sc%2==0){
		/* even case skip */
		align_cells(blk, lvl+1);
		return;
	}

	ic = sp[lvl].i;
	jc = sp[lvl].j;

	/* recursive cases */
	pnls = sp[lvl].count/2;
	printf("ic=%d jc=%d lvl=%d pnls=%d\n", ic, jc, lvl, pnls);

	for(j=0; j<=pnls; j++) {
		for(i=0; i<pnls; i++) {
			k = 2*i + ((i>=j)?1:0);
			tbl[jc][ic-sc+k] = 2;
			tbl[jc][ic-sc+k+1] = 3;
		}
		tbl[jc][ic-sc+2*j] = 0;

		printf("&\n");
		print_block(blk);
		best_sofar = blk->best_align;
		hope_for = align_score(blk);
		printf("best_sofar=%d hope_for=%d\n", best_sofar, hope_for);

		if (best_sofar < hope_for)
			align_cells(blk, lvl+1);

	}

	printf("\n");

	/* clear table belore leaving */
	for(i=0; i<sc; i++)
		tbl[jc][ic-sc+i] = 1;
	
}

void grid(room r, cell* c,int* n)
{
int maxs, offs, line;
int maxb, offb;
point crn;
box bb;
int *scr;
int w, h;
int i, j, jh, ib=0, hsize;
int jc, ic, sc, k;
int top, btm, count;

	bounding_box(&r.walls, &bb);
	crn = (point){bb.xmin, bb.ymin};

	w = ceil((bb.xmax - bb.xmin)/50);
	h = ceil((bb.ymax - bb.ymin - 60)/5);
	
	int tbl[10][h][w];
	int score[10][h];
	int bst[h][w];

	*n = 0;

	/* scan offsets */
	maxb = 0;
	for(offs=0; offs<10; offs++) {
	
		/* create grid */
		fill_matrix(offs, crn, &r, &tbl[offs], w, h);

		memset(&score[offs], 0, h*sizeof(int));

		/* eval score */
		maxs = 0;
		for(j=0; j<h; j++) {
			line = count_row(tbl[offs][j], w, NULL, 0);
			maxs = MAX(line + ((j>12)?score[offs][j-12]:0), maxs);
			score[offs][j] = maxs;
		}

		/* get the best offset */
		if (maxs > maxb) {
			maxb = maxs;
			offb = offs;
		}
		
	}

	table.tbl = tbl[offb];
	table.score = score[offb];
	table.w = w;
	table.h = h;

	print_table();

	/* select rows */
	j = h-1;
	scr = score[offb];
	str heap[h];
	str *ph = heap;

	/* select rows */
	while(j>=0 && scr[j]>0) {

		while(j>0 && scr[j]==scr[j-1])
			j--;

		/* get line */
		count_row(tbl[offb][j], w, &ph, j);
		
		/* next row */
		j -= 12;
	}


	/* group in blocks */
	block blk[h];
	hsize = ph-heap;
	j = 0;

	printf("\n===> STR  <==================\n");
	for(i=0; i<hsize; i++)
		printf("%2d. j=%d\n ", i, heap[i].j);

	while(j<hsize) {
		/* prepare block */
		blk[ib].sp = &heap[j]; 
		blk[ib].size  = 0;
		blk[ib].best_align = -1;
		blk[ib].tbl = &bst;

		/* find last str */
		do {
			blk[ib].size++;
			jh = heap[j].j;
			j++;
		}
		while(j<hsize && jh-heap[j].j<=12);

		/* next block */
		ib++;
	}

	printf("\n===> BLOCKS <==================\n");

	/* allocate even strings */
	for(i=0; i<ib; i++) {
		printf("block %d %d\n", i, blk[i].size);
		for(j=0; j<blk[i].size; j++) {
			sc = blk[i].sp[j].count;
			if (sc%2!=0)
				continue;

			ic = blk[i].sp[j].i;
			jc = blk[i].sp[j].j;

			for(k=0; k<sc; k+=2) {
				tbl[offb][jc][ic-sc+k] = 2;
				tbl[offb][jc][ic-sc+k+1] = 3;
			}

			printf("\t (%d,%d) %d\n", 
				blk[i].sp[j].i, 
				blk[i].sp[j].j,
				blk[i].sp[j].count);
		}
	}
	
	for(k=0; k<ib; k++)
	{
		iter = 0;
		align_cells(&blk[k], 0);	
		printf("iter=%d\n", iter);
		print_best_bl(&blk[k]);

		top = blk[k].sp[0].j;
		btm = blk[k].sp[blk[k].size-1].j;

		/* draw aligned cells */
		typedef int (*table_p)[w];
		table_p tbl = (table_p)(blk[k].tbl);	

		for(j=top; j>=btm; j-=12) {
			count = 0;
			for(i=0; i<w; i++) {
				if (tbl[j][i]==2) {
					count++;
					c[*n].row  = j;
					c[*n].col  = i;
					c[*n].x = 5*offb + i*50 + bb.xmin;
					c[*n].y = 5*j + bb.ymin;
					(*n)++;
				}
			}
		}
	}



}



int main() {

	polygon pgon;
	box mbox;

	pgon.poly = (point*)malloc(7*sizeof(point));
	pgon.poly[0] = (point){0,0};
	pgon.poly[1] = (point){1,0};
	pgon.poly[2] = (point){1,1};
	pgon.poly[3] = (point){2,1};
	pgon.poly[4] = (point){2,2};
	pgon.poly[5] = (point){0,2};
	pgon.poly[6] = (point){0,0};
	pgon.len = 7;

	mbox.xmin = 1.7;
	mbox.xmax = 2.01;
	mbox.ymin = 1.7;
	mbox.ymax = 2;

	if (check_box(INSIDE, &mbox, &pgon)) {
		printf("INSIDE\n");
	} else {
		printf("OUTSIDE\n");
	}

}



