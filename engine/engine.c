#include <float.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "engine.h"
#include "cairo_drawing.h"

uint32_t __score;

panel_desc_t panel_desc[] =
{
	{200., 120., 2.4, 1024, 4, "full",   40, 60, 0xC000, 0xB000},
	{200., 120., 2.4, 1024, 4, "lux",    40, 60, 0x3000, 0x2000},
	{200.,  60., 1.2, 511, 4, "split",   40, 30, 0x0C00, 0x0800},
	{100., 120., 1.2, 511, 2, "half",    20, 60, 0x0300, 0x0200},
	{100.,  60., 0.6, 254, 2, "quarter", 20, 30, 0x00C0, 0x0080},
};

#define ALL_FAIL  0xFFC0

config_t config = {
	.debug = 0,
	.enable_fulls = 1,
	.enable_lux = 1,
	.enable_splits = 1,
	.enable_halves = 1,
	.enable_quarters = 1,
	.max_row_debug = 10000,
	.debug_animation = 0,
	.one_direction = 0,
	.lux_width = LUX_WIDTH,
	.lux_height = LUX_HEIGHT
};

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
uint32_t dorsal_row = 0;

	for(dorsal_t* d=alloc->dorsals; d!=NULL; d=d->next)  {
		for(int k=0; k<d->num_panels; k++) {
			np = (panel_t*)malloc(sizeof(panel_t));
			*np = d->panels[k];
			np->next = head;
			head = np;
			np->orient_flags = 0;
			np->dorsal_row = dorsal_row;
		}
		dorsal_row++;
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

int __flag;

int fit(panel_t* p, room_t* room, uint16_t* flag)
{
int i, m1, m2, n1, n2;
box_t box, lux_box;
double x,y;
uint8_t (*gv)[p->grid->cols] = p->grid->_gridv;
uint8_t (*gh)[p->grid->cols] = p->grid->_gridh;
polygon_t *pgon;

	n1 = (int)p->row;
	m1 = (int)p->col;
	n2 = n1 - (int)panel_desc[p->type].y_steps;
	m2 = m1 - (int)panel_desc[p->type].x_steps;

	if (m2<0 || n2<0) 
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

			lux_box.xmin = (box.xmin + box.xmax - config.lux_width)/2;
			lux_box.xmax = (box.xmin + box.xmax + config.lux_width)/2;
			lux_box.ymin = (box.ymin + box.ymax - config.lux_height)/2;
			lux_box.ymax = (box.ymin + box.ymax + config.lux_height)/2;

			for(int j=0; j<pgon->len-1; j++) 
				if (!point_inside_box(&pgon->poly[j], &lux_box))
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
int w = (int)panel_desc[panel->type].x_steps;
int h = (int)panel_desc[panel->type].y_steps;
int gap1_left, gap2_left;
int gap1_right, gap2_right;
int i1, i2;

	uint32_t (*gaps)[alloc->wall_grid.cols] = alloc->wall_grid.gaps;

	i1 = pos.i;
	i2 = i1 - LID_STEPS;
	if (panel->heading == DOWN) {
		i1 -= h;
		i2 = i1 + LID_STEPS;
	}

	gap1_left = gaps[i1][pos.j-w];
	gap2_left = gaps[i2][pos.j-w];
	gap1_right = gaps[i1][pos.j];
	gap2_right = gaps[i2][pos.j];

	/* check if gaps are consistent */
	if (gap1_left < DIST_FROM_WALLS || 
		gap2_left < DIST_FROM_WALLS)
		return 0;

	if (pos.j > STEPS_RIGHT_GAP) {
		if (gap1_right < DIST_FROM_WALLS || 
			gap2_right < DIST_FROM_WALLS)
			return 0;
	}

	/* find the minium gap */
	if (gap1_left < alloc->gap)
		alloc->gap = gap1_left;

	if (gap2_left < alloc->gap)
		alloc->gap = gap2_left;

	if (gap1_right < alloc->gap)
		alloc->gap = gap1_right;

	if (gap2_right < alloc->gap)
		alloc->gap = gap2_right;

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
grid_pos_t pos, tpos;
dorsal_width_t width;
heading_t dir;
int max_score = 0, new_score;
int score = 0;
int num_panels, k=0, kp, type;
uint16_t *flag, panel_done, panel_fail;
uint32_t parity;
int level;
	uint32_t (*bounds)[2] = alloc->wall_grid.bounds;
	uint16_t (*flags)[alloc->wall_grid.cols] = alloc->wall_grid.flags;

	dorsal->score = 0;
	width = dorsal->width;
	dir = dorsal->heading;

	pos.grid = &alloc->wall_grid;
	pos.i = dorsal->offset_row;
	pos.j = dorsal->offset_col;

	level = pos.i;
	parity = dorsal->parity;

	if (dir==DOWN) {
		level = pos.i - HD_STEPS*((width==NARROW)?1:2);
		if (level<0) {
			dorsal->num_panels = 0;
			return 0;
		}
	}

	while(pos.j < bounds[level][0] + 2*INTER_RAIL_STEPS)
		pos.j += INTER_RAIL_STEPS;

	while(pos.j<= bounds[level][1]) {

		// parity = ((k+v)&3)>>1;
		//printf("%d ", parity);

		/* tpos = pos; */

		/* flag = &flags[pos.i][pos.j]; */

		/* /1* skip all panels if they already failed *1/ */
		/* if ((*flag & ALL_FAIL) == ALL_FAIL) */
		/* 	goto next; */

		panel_fail = 0x4000;
		panel_done = 0x8000;

		for(type=0; type<NUM_PANEL_T; type++){

			if ((!config.enable_fulls && type==FULL) ||
				(!config.enable_lux && type==LUX) ||
				(!config.enable_splits && type==SPLIT) ||
				(!config.enable_halves && type==HALF) ||
				(!config.enable_quarters && type==QUARTER)) {
					panel_fail >>= 2;
					panel_done >>= 2;
					continue;
			}

			/* skip panel type if dorsal does not support panel*/
			if (width==NARROW && 
			    (type==FULL || type==LUX || type==HALF)) {

				panel_fail >>= 2;
				panel_done >>= 2;
				continue;
			}

			tpos = pos;
			if (width== WIDE && dir==DOWN && (type==SPLIT || type==QUARTER))
				tpos.i -= HD_STEPS;

			flag = &flags[tpos.i][tpos.j]; 

			/* skip panel if check already failed for it */
			if (*flag & panel_fail) {
				panel_fail >>= 2;
				panel_done >>= 2;
				continue;
			}

			/* test if panel fit */
			panel(&trial, type, tpos, dir);
		
			if ( ((*flag & panel_done) || fit(&trial, room, flag)) 
				 && gap_ok(&trial, tpos, alloc)) {

					new_score = panel_desc[type].score;
					kp = k - panel_desc[type].prev;
					if (kp>=0)
						new_score += _panels[kp].score;
			
					if (new_score>max_score ||
						(new_score==max_score && parity)) {
						max_score = new_score;
						_panels[k] = trial;
					}	
			}
			panel_fail >>= 2;
			panel_done >>= 2;
		}
		_panels[k].score = max_score;

		k++;
		pos.j += INTER_RAIL_STEPS;
	}
	

	k--;
	if (k>=0)
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
int k=HD_STEPS, kp[2], ke[2];
uint32_t dorsal_score, eval;
dorsal_t trial;
dorsal_t *dors_up = alloc->_dors_up;
dorsal_t *dors_down = alloc->_dors_down;
dorsal_t *dorsal;
dorsal_score_t* score = alloc->_dorsal_score;
int rows;

	alloc->dorsals = NULL;
	trial.offset_col = alloc->offset_col;
	rows = alloc->wall_grid.rows;

	if (HD_STEPS>=rows) 
		return 0;

	for(k=HD_STEPS; k < rows; k++) {

		kp[NARROW] = k - HD_STEPS;
		kp[WIDE]   = MAX(k - 2*HD_STEPS, 0);
		ke[NARROW] = MAX(kp[NARROW] - INTER_DORSAL_GAP, 0);
		ke[WIDE]   = MAX(kp[WIDE] - INTER_DORSAL_GAP, 0);

		for(int width=0; width<2; width++) {

			/* calculate score of current dorsal */
			trial.width = width;
			trial.offset_row = k;

			/* evaluating up dorsals */
			trial.heading = UP;
			trial.parity = dors_up[kp[width]].parity ^ 1;
			dorsal_score = make_dorsal(alloc, &trial);
			eval = dorsal_score + dors_up[kp[width]].score;
			if (eval > dors_up[k].score) {
				dors_up[k] = trial;
				dors_up[k].score = eval;
				dors_up[k].next = &dors_up[kp[width]];
			}
	
			eval = dorsal_score + dors_down[kp[width]].score;
			if (eval > dors_up[k].score) {
				dors_up[k] = trial;
				dors_up[k].score = eval;
				dors_up[k].next = &dors_down[kp[width]];	
			}

			eval = dorsal_score + score[ke[width]].score;
			if (eval > dors_up[k].score) {
				dors_up[k] = trial;
				dors_up[k].score = eval;
				dors_up[k].next = score[ke[width]].dorsal;	
			}

			/* evaluating down dorsals */
			trial.heading = DOWN;
			trial.parity = dors_down[kp[width]].parity ^ 1;
			dorsal_score = make_dorsal(alloc, &trial);
	
			eval = dorsal_score + dors_down[kp[width]].score;
			if (eval > dors_down[k].score) {
				dors_down[k] = trial;
				dors_down[k].score = eval;
				dors_down[k].next = &dors_down[kp[width]];	
			}

			eval = dorsal_score + score[ke[width]].score;
			if (eval > dors_down[k].score) {
				dors_down[k] = trial;
				dors_down[k].score = eval;
				dors_down[k].next = score[ke[width]].dorsal;
			}
		}

		score[k].dorsal = score[k-1].dorsal;
		score[k].score = score[k-1].score;

		if (dors_up[k].score > dors_down[k].score)
			dorsal = &dors_up[k];
		else
			dorsal = &dors_down[k];

		if (dorsal->next == NULL) 
			continue;
		
		/* eval = dorsal->next->score; */
		if (dorsal->score > score[k].score)
			/* ||  (dorsal->score == score[k].score && eval==0)) */ 
		{
				score[k].dorsal = dorsal;
				score[k].score = dorsal->score;
		}
	}
	alloc->dorsals = score[k-1].dorsal;

	return score[k-1].score;
}


uint32_t search_offset(allocation_t* alloc)
{
box_t *box = &alloc->wall_grid.box;
point_t offset;
uint32_t max_score = 0, score, rows;
double gap = 0;

	rows = alloc->wall_grid.rows;
	alloc->panels = NULL;
	offset = (point_t){box->xmin, box->ymin};

	for(int k=0; k<NUM_OFFSETS; k++) {
		alloc->offset = offset;
		alloc->gap = DBL_MAX;
		alloc->offset_col = k;

		/* reset scoreboards */
		memset(alloc->_dors_up, 0, rows*sizeof(dorsal_t));
		memset(alloc->_dors_down, 0, rows*sizeof(dorsal_t));
		memset(alloc->_dorsal_score, 0, rows*sizeof(dorsal_score_t));

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

	alloc->gap = gap;
	return max_score;
}


panel_t* panel_room(room_t* room, uint32_t* score)
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
	/* ); */

	alloc._dors_up = malloc(sizeof(dorsal_t)*grid->rows);
	alloc._dors_down = malloc(sizeof(dorsal_t)*grid->rows);
	alloc._dorsal_score = 
		malloc(sizeof(dorsal_score_t)*grid->rows);

	*score = __score = search_offset(&alloc);

	free(alloc._dorsal_score);
	free(alloc._dors_down);
	free(alloc._dors_up);
	free_grid(grid);

	return alloc.panels;
}

void copy_room(room_t* room_in, room_t* room_out)
{
int len = room_in->obs_num;

	copy_polygon(&room_in->walls,&room_out->walls);
	room_out->obs_num = len;
	room_out->collector_pos = room_in->collector_pos;
	room_out->obstacles = malloc(sizeof(polygon_t)*len);
	for(int i=0; i<len; i++)
		copy_polygon(&room_in->obstacles[i], 
				&room_out->obstacles[i]);

}

void free_room(room_t* room)
{
	free(room->obstacles);
}

void set_orient_flags(panel_t* head)
{
ptype pt;
panel_t* pn;
	
	for(pn=head; pn!=NULL; pn=pn->next){ 
		
		pt = pn->type;
		if (pn->heading == DOWN) {
			pn->orient_flags |= INVERT;
			pn->pos.x -= panel_desc[pt].width;
			pn->pos.y -= panel_desc[pt].height;
		}
	}

}


panel_t* build_room(room_t* room)
{
double t;
room_t trial_room;
panel_t *panels_upright, *panels_flat, *pn;
panel_t *pnls_sel;
uint32_t upright_score=0, flat_score=0;
point_t point;

	/* calculate panel flats */
	panels_flat = panel_room(room, &flat_score);
	set_orient_flags(panels_flat);

	if (config.one_direction==1) 
		return panels_flat;


	/* calculate panels upright*/
	copy_room(room, &trial_room);

	// mirror with respect to y=-x
	for(int i=0; i<room->walls.len; i++) {
		t = room->walls.poly[i].x;
		trial_room.walls.poly[i].x = -trial_room.walls.poly[i].y;
		trial_room.walls.poly[i].y = -t;
	}

	for(int i=0; i<room->obs_num; i++) {
		for(int k=0; k<room->obstacles[i].len; k++) {
			t = room->obstacles[i].poly[k].x;
			trial_room.obstacles[i].poly[k].x =
				-trial_room.obstacles[i].poly[k].y;
			trial_room.obstacles[i].poly[k].y = -t;
		}
	}

	panels_upright = panel_room(&trial_room, &upright_score);
	set_orient_flags(panels_upright);

	if (config.debug) {
		draw_room(&trial_room);
		draw_panels(panels_upright);
	}

	// back rotate panels 
	for(pn=panels_upright; pn!=NULL; pn=pn->next){

		point = (point_t){-panel_desc[pn->type].width, 0.};
		point = rotate(point, pn->orient_flags);
		point = (point_t){point.x+pn->pos.x, point.y + pn->pos.y};

		pn->pos.x = -point.y;
		pn->pos.y = -point.x;
		pn->orient_flags = pn->orient_flags ^ 0x00000001;

	}

	free_room(&trial_room);

	pnls_sel = (upright_score > flat_score || config.one_direction==2) ?
		panels_upright:panels_flat;


	return pnls_sel; 
}





