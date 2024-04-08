#include "engine.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


canvas_t * __debug_canvas;

panel_desc_t panel_desc[] =
{
	{200., 120., 1024, 4, "full"},
	{200., 120., 1024, 4, "lux"},
	{200.,  60.,  511, 4, "split"},
	{100., 120.,  511, 2, "half"},
	{100.,  60.,  254, 2, "quarter"}
};


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


int gap_ok(panel_t *panel, room_t *r)
{
point_t ref_point;
double w = panel_desc[panel->type].width;
double h = panel_desc[panel->type].height;

	ref_point = (point_t){panel->pos.x-w, panel->pos.y};
	if (panel->heading == DOWN) 
		ref_point.y -= h;
	
	if (hdist(&ref_point, &(r->walls))<DIST_FROM_WALLS)
		return 0;

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


uint32_t make_dorsal(room_t* room, dorsal_t* dorsal) 
{
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
	
	while(ofs.x < room->box.xmax) {

		for(type=0; type<NUM_PANEL_T; type++){

			if (width==NARROW && 
			   (type==FULL || type==LUX || type==HALF))
				continue;
			
			ref_point = ofs;
			if (dir == DOWN && width==WIDE &&
				(type == SPLIT || type==QUARTER))
				ref_point.y -= 60;

			panel(&trial, type, ref_point, dir);
			if (fit(&trial, room) && gap_ok(&trial, room)) {
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

uint32_t scanline(room_t* room)
{
int k=0, kp;
uint32_t score, max_score = 0, new_score;
point_t ofs;
dorsal_t dorsals[200], trial;

	ofs = (point_t){room->box.xmin, room->box.ymin};
	while(ofs.y < room->box.ymax) {

		trial.offset = ofs;
		trial.width = WIDE;
		trial.heading = UP;
		new_score = make_dorsal(room, &trial);
		kp = k - 12;
		if (kp>=0)
			new_score += dorsals[kp].score;
		if (new_score>max_score) {
			max_score = new_score;
			dorsals[k] = trial;
			//draw_panels(__debug_canvas, lines[k].panels);
		}

		dorsals[k].score = max_score;
		ofs.y += INTER_LINE_GAP;
		k++;
	}

	k--;
	score = dorsals[k].score;

	while(k>=0 && score>0) {

		if (k==0 || dorsals[k-1].score<score) {
			draw_panels(__debug_canvas, &dorsals[k]);
			k -= 12;
			score = dorsals[k].score; 
			continue;
		}  
		k--;
	}

	return max_score;
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
void draw_panels(canvas_t*cp, dorsal_t* dorsal)
{
	for(int i=0; i<dorsal->num_panels; i++)
		draw_panel(cp, &dorsal->panels[i]);

}

