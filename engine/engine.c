#include "engine.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


canvas_t * __debug_canvas;

panel_desc_t panel_desc[] =
{
	{200., 120., 2.4, 1024, 4, "full",   40, 60, 0xC000, 0xB000},
	{200., 120., 2.4, 1024, 4, "lux",    40, 60, 0x3000, 0x2000},
	{200.,  60., 1.2, 511, 4, "split",   40, 30, 0x0C00, 0x0800},
	{100., 120., 1.2, 511, 2, "half",    20, 60, 0x0300, 0x0200},
	{100.,  60., 0.6, 254, 2, "quarter", 20, 30, 0x00C0, 0x0080},
};

#define ALL_FAIL  0xFFC0

int count_panels(panel_t* head)
{
	int tot = 0;
	for(panel_t* p=head; p!=NULL; p=p->next)
		tot++;

	return tot;
}

panel_t* copy_panels(allocation_t* alloc)
{
panel_t* head = NULL, *np;
int num_dorsals=0, mallocs=0;

	for(dorsal_t* d=alloc->dorsals; d!=NULL; d=d->next)  {
		for(int k=0; k<d->num_panels; k++) {
			np = (panel_t*)malloc(sizeof(panel_t));
			mallocs++;
			*np = d->panels[k];
			np->next = head;
			head = np;
		}
		num_dorsals++;
	}
	return head;
}

void free_panels(panel_t* head)
{
panel_t *p = head, *q;

	while(p!=NULL) {
		q = p->next;
		free(p);
		p = q;
	}

}

double active_area(panel_t* head)
{
	double tot = 0;
	
	for(panel_t* p=head; p!=NULL; p=p->next)
		tot += panel_desc[p->type].active_area;

	return tot;
}

int fit(panel_t* p, room_t* room, uint16_t* flag)
{
int i, m1, m2, n1, n2;
box_t box, lux_box;
double x,y;
uint8_t (*gv)[p->grid->cols] = p->grid->_gridv;
uint8_t (*gh)[p->grid->cols] = p->grid->_gridh;
polygon_t *pgon;


	n1 = p->row;
	m1 = p->col;
	n2 = n1 - panel_desc[p->type].y_steps;
	m2 = m1 - panel_desc[p->type].x_steps;

	if (m2<0 || n2<=0)
		goto fail;

	if (!((gv[n1][m1] & 0x01) &&
			gh[n1][m1] == gh[n1][m2] && 
			gv[n1][m2] == gv[n2][m2] &&
			gh[n2][m2] == gh[n2][m1] &&
			gv[n2][m1] == gv[n1][m1] )) 
		goto fail;

	for(i=0; i<room->obs_num; i++) {
		pgon = &room->obstacles[i];
		x = pgon->poly[0].x;
		y = pgon->poly[0].y;
	
		box = p->pbox;
		if (p->pbox.xmin<x && x<p->pbox.xmax &&
			p->pbox.ymin<y && y<p->pbox.ymax) {
			if (!(p->type == LUX)) 
				goto fail;

			lux_box.xmin = (box.xmin + box.xmax - LUX_WIDTH)/2;
			lux_box.xmax = (box.xmin + box.xmax + LUX_WIDTH)/2;
			lux_box.ymin = (box.ymin + box.ymax - LUX_HEIGHT)/2;
			lux_box.ymax = (box.ymin + box.ymax + LUX_HEIGHT)/2;

			for(int i=1; i<pgon->len-1; i++)
				if (!point_inside_box(&pgon->poly[i], &lux_box))
					goto fail;	
		}
	}

	*flag |= panel_desc[p->type].done_ok;
	return 1;

fail:
	*flag |= panel_desc[p->type].done_fail;
	return 0;
}


int gap_ok(panel_t *panel, grid_pos_t pos, allocation_t *alloc)
{
int w = panel_desc[panel->type].x_steps;
int h = panel_desc[panel->type].y_steps;
int gap_left;
uint32_t i;

	uint32_t (*gaps)[alloc->wall_grid.cols] = alloc->wall_grid.gaps;

	i = pos.i;
	if (panel->heading == DOWN)
		i -= h;

	gap_left = gaps[i][pos.j-w];

	if (gap_left < DIST_FROM_WALLS)
		return 0;

	if (gap_left < alloc->gap)
		alloc->gap = gap_left;

	return 1;
}


void panel(panel_t* pp, ptype pt, grid_pos_t pos, heading_t ht)
{
double x,y;

	pp->grid = pos.grid;
	pp->row = pos.i;
	pp->col = pos.j;
	x = pos.grid->origin.x + pos.j*pos.grid->x_step;
	y = pos.grid->origin.y + pos.i*pos.grid->y_step;

	pp->type = pt;
	pp->pos = (point_t){x, y};
	pp->heading = ht;
	pp->next = NULL;
	pp->score = 0;
	pp->pbox.xmax = x;
	pp->pbox.ymax = y;
	if (pt==FULL || pt==SPLIT || pt==LUX)
		pp->pbox.xmin = x - 200;
	else
		pp->pbox.xmin = x - 100;

	if (pt==FULL || pt==HALF || pt==LUX)
		pp->pbox.ymin = y - 120;
	else
		pp->pbox.ymin = y - 60;
}


uint32_t make_dorsal(allocation_t* alloc, dorsal_t* dorsal) 
{
room_t* room = alloc->room;
panel_t _panels[MAX_RAILS];
panel_t trial;
grid_pos_t pos;
dorsal_width_t width;
heading_t dir;
int max_score = 0, new_score;
int score;
int num_panels, k=0, kp, type;
uint16_t *flag, panel_done, panel_fail;

	uint32_t (*bounds)[2] = alloc->wall_grid.bounds;

	uint16_t (*flags)[alloc->wall_grid.cols] = alloc->wall_grid.flags;

	width = dorsal->width;
	dir = dorsal->heading;

	pos.grid = &alloc->wall_grid;
	pos.i = dorsal->offset_row;
	pos.j = dorsal->offset_col;

	while(pos.j < bounds[pos.i][0] + 2*INTER_RAIL_STEPS)
		pos.j += INTER_RAIL_STEPS;

	while(pos.j<= bounds[pos.i][1]) {

		flag = &flags[pos.i][pos.j];

		/* skip all panels if they already failed */
		if ((*flag & ALL_FAIL) == ALL_FAIL)
			goto next;

		panel_fail = 0x4000;
		panel_done = 0x8000;

		for(type=0; type<NUM_PANEL_T; type++){

			/* skip panel type if dorsal does not support panel*/
			if (width==NARROW && 
			    (type==FULL || type==LUX || type==HALF)) {

				panel_fail >>= 2;
				panel_done >>= 2;
				continue;
			}

			/* skip panel if check already failed for it */
			if (*flag & panel_fail) {
				panel_fail >>= 2;
				panel_done >>= 2;
				continue;
			}

			/* test if panel fit */
			panel(&trial, type, pos, dir);
		
			if ( ((*flag & panel_done) || fit(&trial, room, flag)) 
				 && gap_ok(&trial, pos, alloc)) {

					new_score = panel_desc[type].score;
					kp = k - panel_desc[type].prev;
					if (kp>=0)
						new_score += _panels[kp].score;
				
					if (new_score>max_score) {
						max_score = new_score;
						_panels[k] = trial;
					}	
			}
			panel_fail >>= 2;
			panel_done >>= 2;
		}
next:
		_panels[k].score = max_score;

		k++;
		pos.j += INTER_RAIL_STEPS;
	}

	k--;
	score = dorsal->score = _panels[k].score;

	num_panels = 0;
	while(k>=0 && score>0) {

		if (k==0 || _panels[k-1].score<score) {
			dorsal->panels[num_panels] = _panels[k];
			num_panels++;
			k -= panel_desc[_panels[k].type].prev;
			score = _panels[k].score; 
			continue;
		}  
		k--;	
	}

	dorsal->num_panels = num_panels;
	return dorsal->score;
}

int len(panel_t* p)
{
	int tot = 0;
	while(p!=NULL) {
		p = p->next;
		tot++;
	}
	return tot;
}

int count_dorsals(dorsal_t* head)
{
	int tot=0;
	for(dorsal_t* dorsal=head; dorsal!=NULL; dorsal=dorsal->next)
		tot++;

	return tot;
}

uint32_t scanline(allocation_t* alloc)
{
int k=0, kp;
uint32_t max_score = 253, new_score;
dorsal_t trial, *dorsals = alloc->_dorsals;
point_t ofs = alloc->offset;
uint32_t mark=-1;
int rows;

	alloc->dorsals = NULL;
	trial.offset_col = alloc->offset_col;
	rows = alloc->wall_grid.rows;

	while(k < rows) {

		dorsals[k].num_panels = 0;
		dorsals[k].next = alloc->dorsals;

		if (k<=HD_STEPS)
			goto next;

		for(int width=0; width<2; width++)
			for(int head=0; head<2; head++) {
				trial.offset = ofs;
				trial.width = width;
				trial.heading = head;
				trial.offset_row = k;
				new_score = make_dorsal(alloc, &trial);

				kp = (width==WIDE)?(k - 2*HD_STEPS):
				                   (k - HD_STEPS);

				if (kp>=0 && dorsals[kp].num_panels>0) {
					new_score += dorsals[kp].score;
					trial.next = &dorsals[kp];
				} else {
					kp -= INTER_DORSAL_GAP;
					trial.next = (kp>=0)?&dorsals[kp]:NULL;
					if (trial.next)
						new_score += dorsals[kp].score;
				}
				if (new_score>max_score ||
					(new_score==max_score && k>mark &&
					 k<rows/2)) {
					max_score = new_score;
					dorsals[k] = trial;
					alloc->dorsals = &dorsals[k];
					mark = k;
				}
			}
next:
		dorsals[k].score = max_score;

		ofs.y += INTER_LINE_GAP;
		k++;
	}

	return max_score;

}

uint32_t search_offset(allocation_t* alloc)
{
box_t *box = &alloc->wall_grid.box;
point_t offset;
uint32_t max_score = 0, score;
double gap = 0;

	alloc->panels = NULL;
	offset = (point_t){box->xmin, box->ymin};
	for(int k=0; k<NUM_OFFSETS; k++) {

		alloc->offset = offset;
		alloc->gap = 0;
		alloc->offset_col = k;

		score = scanline(alloc);
		if (score>max_score || 
		    ((score == max_score) && alloc->gap > gap)) {
			max_score = score;
			gap = alloc->gap;

			/* copy dorsals */
			if (alloc->panels)
				free_panels(alloc->panels);
			alloc->panels = copy_panels(alloc);
		}

		offset.x += OFFSET_STEP;
		
	}

	return max_score;
}


panel_t* panel_room(room_t* room)
{
allocation_t alloc;
grid_t* grid = &alloc.wall_grid;

	alloc.room = room;

	grid->poly = &room->walls;
	grid->x_step = OFFSET_STEP;
	grid->y_step = INTER_LINE_GAP;
	//build_grid(wall_grid);
	init_grid(grid);
	update_grid(grid, 1);

	for(int i=0; i<room->obs_num; i++) {
		grid->poly = &room->obstacles[i];
		update_grid(grid, 0);
	}

	/* printf("cols=%d, rows=%d x_step=%.3lf y_step=%.3lf\n", */ 
	/* 	grid->cols, grid->rows, */
	/* 	grid->x_step, grid->y_step); */

	/* printf("xmin=%.3lf xmax=%.3lf ymin=%.3lf ymax=%.3lf\n", */ 
	/* 		grid->box.xmin, */
	/* 		grid->box.xmax, */
	/* 		grid->box.ymin, */
	/* 		grid->box.ymax */
	/* 		); */

	alloc._dorsals = malloc(sizeof(dorsal_t)*grid->rows);

	search_offset(&alloc);
	free_grid(grid);
	free(alloc._dorsals);

	return alloc.panels;
}


/* libcairo drawing support */

void draw_room(canvas_t* ct, room_t *rp) {
int i;
	
	draw_polygon(ct, &rp->walls, BLUE);
	for(i=0; i<rp->obs_num; i++)
		draw_polygon(ct, &rp->obstacles[i], YELLOW);

}

void draw_rect(canvas_t* ct, box_t* box, colour_t col)
{
point_t poly[5];
polygon_t pgon;
	
	pgon.len = 5;
	pgon.poly = (point_t*)poly;
	poly[0] = (point_t){box->xmin, box->ymin};
	poly[1] = (point_t){box->xmin, box->ymax};
	poly[2] = (point_t){box->xmax, box->ymax};
	poly[3] = (point_t){box->xmax, box->ymin};
	poly[4] = poly[0];

	draw_polygon(ct, &pgon, col);
}

void draw_panel(canvas_t* ct, panel_t* p) 
{
point_t centre;
box_t box;

point_t poly[9];
polygon_t pgon;
	
	pgon.len = 9;
	pgon.poly = (point_t*)poly;
	poly[0] = (point_t){p->pbox.xmin, p->pbox.ymin};
	poly[1] = (point_t){p->pbox.xmin, p->pbox.ymax-EDGE};
	poly[2] = (point_t){p->pbox.xmin+EDGE, p->pbox.ymax-EDGE};
	poly[3] = (point_t){p->pbox.xmin+EDGE, p->pbox.ymax};
	poly[4] = (point_t){p->pbox.xmax-EDGE, p->pbox.ymax};
	poly[5] = (point_t){p->pbox.xmax-EDGE, p->pbox.ymax-EDGE};
	poly[6] = (point_t){p->pbox.xmax, p->pbox.ymax-EDGE};
	poly[7] = (point_t){p->pbox.xmax, p->pbox.ymin};
	poly[8] = poly[0];

	if (p->heading == DOWN)
		for(int i=0; i<9; i++) 
			poly[i].y = p->pbox.ymax + p->pbox.ymin - poly[i].y;

	draw_polygon(ct, &pgon, GREEN);

	if (p->type == LUX) {
		centre = (point_t){
			(p->pbox.xmin+p->pbox.xmax)/2,
			(p->pbox.ymin+p->pbox.ymax)/2
		};
		box.xmin = centre.x - LUX_WIDTH/2;
		box.xmax = centre.x + LUX_WIDTH/2;
		box.ymin = centre.y - LUX_HEIGHT/2;
		box.ymax = centre.y + LUX_HEIGHT/2;
		draw_rect(ct, &box, GREEN);
	}
}
void draw_dorsal(canvas_t*cp, dorsal_t* dorsal)
{
	for(int i=0; i<dorsal->num_panels; i++)
		draw_panel(cp, &dorsal->panels[i]);
}

void draw_panels(canvas_t*cp, panel_t* panels)
{
	for(panel_t* p=panels; p!=NULL; p=p->next) 
		draw_panel(cp, p);
}



