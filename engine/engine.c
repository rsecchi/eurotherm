#include "engine.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


canvas_t * __debug_canvas;

panel_desc_t panel_desc[] =
{
	{200., 120., 2.4, 1024, 4, "full"},
	{200., 120., 2.4, 1024, 4, "lux"},
	{200.,  60., 1.2, 511, 4, "split"},
	{100., 120., 1.2, 511, 2, "half"},
	{100.,  60., 0.6, 254, 2, "quarter"}
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

int fit(panel_t* p, room_t* r)
{
int i;
box_t box, lux_box;

	box = p->pbox;

	/* check if inside room */
	if (!check_box(INSIDE, &p->pbox, &r->walls))
		return 0;

	if (p->type == LUX) {

		lux_box.xmin = (box.xmin + box.xmax - LUX_WIDTH)/2;
		lux_box.xmax = (box.xmin + box.xmax + LUX_WIDTH)/2;
		lux_box.ymin = (box.ymin + box.ymax - LUX_HEIGHT)/2;
		lux_box.ymax = (box.ymin + box.ymax + LUX_HEIGHT)/2;

		for(i=0; i<r->obs_num; i++) {
			if (polygon_inside_box(&r->obstacles[i], &lux_box)) 
				continue;

			if (!check_box(OUTSIDE, &box, &r->obstacles[i])) 
				return 0;
		}

		return 1;
	}

	/* check if outside obstacles */
	for(i=0; i<r->obs_num; i++) 
		if (!check_box(OUTSIDE, &box, &(r->obstacles[i])))
			return 0;

	return 1;
}


int gap_ok(panel_t *panel, allocation_t *alloc)
{
room_t* room = alloc->room;
point_t ref_point_left, ref_point_right;
double w = panel_desc[panel->type].width;
double h = panel_desc[panel->type].height;
double gap, gap_left, gap_right;

	ref_point_left  = (point_t){panel->pos.x-w, panel->pos.y};
	ref_point_right = (point_t){panel->pos.x,   panel->pos.y};
	if (panel->heading == DOWN) {
		ref_point_left.y -= h;
		ref_point_right.y -= h;
	}

	gap_left  = hdist(&ref_point_left,  &(room->walls));
	gap_right = hdist(&ref_point_right, &(room->walls));

	if (gap_left<DIST_FROM_WALLS)
		return 0;

	gap = MIN(gap_left, gap_right);
	if (gap < alloc->gap)
		alloc->gap = gap;

	return 1;
}


void panel(panel_t* pp, ptype pt, point_t pos, heading_t ht)
{
	pp->type = pt;
	pp->pos = pos;
	pp->heading = ht;
	pp->next = NULL;
	pp->score = 0;
	pp->pbox.xmax = pos.x;
	pp->pbox.ymax = pos.y;
	if (pt==FULL || pt==SPLIT || pt==LUX)
		pp->pbox.xmin = pos.x - 200;
	else
		pp->pbox.xmin = pos.x - 100;

	if (pt==FULL || pt==HALF || pt==LUX)
		pp->pbox.ymin = pos.y - 120;
	else
		pp->pbox.ymin = pos.y - 60;
}


uint32_t make_dorsal(allocation_t* alloc, dorsal_t* dorsal) 
{
room_t* room = alloc->room;
box_t* box = &alloc->wall_grid.box;
panel_t _panels[MAX_RAILS];
panel_t trial;
point_t ofs, ref_point;
dorsal_width_t width;
heading_t dir;
int max_score = 0, new_score;
int score;
int num_panels, k=0, kp, type;

	ofs = dorsal->offset;
	width = dorsal->width;
	dir = dorsal->heading;
	
	while(ofs.x < box->xmax) {

		for(type=0; type<NUM_PANEL_T; type++){

			if (width==NARROW && 
			   (type==FULL || type==LUX || type==HALF))
				continue;
			
			ref_point = ofs;
			if (dir == DOWN && width==WIDE &&
				(type == SPLIT || type==QUARTER))
				ref_point.y -= 60;

			panel(&trial, type, ref_point, dir);
			if (fit(&trial, room) && gap_ok(&trial, alloc)) {
				new_score = panel_desc[type].score;
				kp = k - panel_desc[type].prev;
				if (kp>=0)
					new_score += _panels[kp].score;
			
				if (new_score>max_score) {
					max_score = new_score;
					_panels[k] = trial;
				}
			}
		}
		_panels[k].score = max_score;

		ofs.x += INTER_RAIL_GAP;
		k++;
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
box_t* box = &alloc->wall_grid.box;
uint32_t max_score = 253, new_score;
dorsal_t trial, *dorsals = alloc->_dorsals;
point_t ofs = alloc->offset;
uint32_t mark=-1;


	alloc->dorsals = NULL;
	while(ofs.y < box->ymax) {

		dorsals[k].num_panels = 0;
		dorsals[k].next = alloc->dorsals;

		for(int width=0; width<2; width++)
			for(int head=0; head<2; head++) {
				trial.offset = ofs;
				trial.width = width;
				trial.heading = head;
				trial.level = k;
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
					 k<alloc->v_steps/2)) {
					max_score = new_score;
					dorsals[k] = trial;
					alloc->dorsals = &dorsals[k];
					mark = k;
				}
			}

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
grid_t* wall_grid = &alloc.wall_grid;

	alloc.room = room;

	wall_grid->poly = &room->walls;
	wall_grid->x_step = OFFSET_STEP;
	wall_grid->y_step = INTER_LINE_GAP;
	build_grid(wall_grid);


	/* printf("%lf %u\n", */
	/* 		alc.box.xmax - alc.box.xmin, */
	/* 		alc.h_steps); */

	/* printf("%lf %u\n", */
	/* 		alc.box.ymax - alc.box.ymin, */
	/* 		alc.v_steps); */

	search_offset(&alloc);

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



