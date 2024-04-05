#include "engine.h"
#include <stdio.h>
#include <string.h>


canvas_t * __debug_canvas;

panel_desc_t panel_desc[] =
{
	{1024, 4, "full"},
	{1024, 4, "lux"},
	{511, 4, "split"},
	{511, 2, "half"},
	{254, 2, "quarter"}
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


void make_line(room_t* room, line_t* line) 
{
panel_t trial, best, panels[MAX_RAILS];
point_t ofs, ref_point;
line_width_t width;
heading_t dir;
int max_score = 0, new_score;
int score, prev_score;
int k = 0, kp, type;

	ofs = line->offset;
	width = line->width;
	dir = line->heading;
	
	memset(panels, 0, MAX_RAILS*sizeof(panel_t));
	
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
			if (fit(&trial, room)) {

				draw_point(__debug_canvas, ofs);
				new_score = panel_desc[type].score;
				kp = k - panel_desc[type].prev;
				if (kp>=0)
					new_score += panels[kp].score;
			
				if (new_score>max_score) {
					max_score = new_score;
					best = trial;
				}
			}
		}
		best.score = max_score;
		panels[k] = best;
		printf("E %d %d %d\n", k, max_score, panels[k].type);

		ofs.x += INTER_RAIL_GAP;
		k++;
	}

	if (max_score==0)
		return;

	k--;

	printf("PRINT LIST\n");
	for(int i=k; i>=0; i--)
		printf("%d %d\n", i, panels[i].score);


	prev_score = panels[k].score;
	printf("INIT: %d\n", prev_score);
	while(k>0 && prev_score>0) {
		printf("<<<  %d >>>>\n", k);
		score = panels[k].score;
		if (score < prev_score) {
			printf("FOUND AT %d %d, type=%d\n", k+1, prev_score,
				panels[k+1].type);
			printf("jumping back of %d\n",panel_desc[panels[k+1].type].prev);  
			draw_panel(__debug_canvas, &panels[k+1]);
			k -= panel_desc[panels[k+1].type].prev;
			if (k<0)
				break;
			prev_score = panels[k+1].score; 
			printf("new k=%d, new prev_score=%d\n", k, prev_score);
		} else {
			printf("%d %d\n", k, score);
			prev_score = score;
			k--;
		}
	}
	if (prev_score>0 && k==0) {
		printf("FOUND AT %d %d\n", k, prev_score);  
		draw_panel(__debug_canvas, &panels[0]);
	}
}

