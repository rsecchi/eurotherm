#include "engine.h"
#include <stdio.h>

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


int gap_is_okay(point_t *q, room_t *r)
{
int i;

	for(i=0; i<4; i++)
		if (hdist(&q[i], &(r->walls))<20.0)
			return 0;

	return 1;
}


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


void panel(panel_t* pp, ptype pt, point_t pos, heading_t ht)
{
	pp->type = pt;
	pp->pos = pos;
	pp->heading = ht;
	pp->pbox.xmin = pos.x;
	pp->pbox.ymin = pos.y;
	if (pt==FULL || pt==SPLIT || pt==LUX)
		pp->pbox.xmax = pos.x + 200;
	else
		pp->pbox.xmax = pos.x + 100;

	if (pt==FULL || pt==HALF || pt==LUX)
		pp->pbox.ymax = pos.y + 120;
	else
		pp->pbox.ymax = pos.y + 60;
}

