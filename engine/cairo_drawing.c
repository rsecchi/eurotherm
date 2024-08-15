#include <string.h>
#include <stdio.h>
#include "engine.h"
#include "geometry.h"
#include "cairo_drawing.h"

canvas_t _canvas;
	
/* libcairo drawing support */

void draw_room(room_t *rp) {
int i;
	
	draw_polygon(&rp->walls, BLUE);
	for(i=0; i<rp->obs_num; i++)
		draw_polygon(&rp->obstacles[i], YELLOW);

}

void draw_rect(box_t* box, colour_t col)
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

	draw_polygon(&pgon, col);
}

void draw_panel(panel_t* p) 
{
double lux_xmin, lux_xmax, lux_ymin, lux_ymax;
point_t poly[9];
point_t lux[5];
polygon_t pgon, plux;
double width, height;
	
	pgon.len = 9;
	pgon.poly = (point_t*)poly;
	width  = panel_desc[p->type].width;
	height = panel_desc[p->type].height;

	poly[0] = (point_t){-width, -height};
	poly[1] = (point_t){-width, -EDGE};
	poly[2] = (point_t){-width+EDGE, -EDGE};
	poly[3] = (point_t){-width+EDGE, 0.};
	poly[4] = (point_t){-EDGE, 0.};
	poly[5] = (point_t){-EDGE, -EDGE};
	poly[6] = (point_t){0., -EDGE};
	poly[7] = (point_t){0., -height};
	poly[8] = poly[0];

	for(int i=0; i<9; i++) { 
		poly[i] = rotate(poly[i], p->orient_flags);
		poly[i].x += p->pos.x;
		poly[i].y += p->pos.y;
	}

	draw_polygon(&pgon, GREEN);

	if (p->type == LUX) {

		lux_xmin = -width/2 - LUX_WIDTH/2;
		lux_xmax = -width/2 + LUX_WIDTH/2;
		lux_ymin = -height/2 - LUX_HEIGHT/2;
		lux_ymax = -height/2 + LUX_HEIGHT/2;

		lux[0] = (point_t){lux_xmin, lux_ymin};
		lux[1] = (point_t){lux_xmin, lux_ymax};
		lux[2] = (point_t){lux_xmax, lux_ymax};
		lux[3] = (point_t){lux_xmax, lux_ymin};
		lux[4] = (point_t){lux_xmin, lux_ymin};
		plux.poly = lux;
		plux.len = 5;

		for(int i=0; i<5; i++) {
			lux[i] = rotate(lux[i], p->orient_flags);
			lux[i].x += p->pos.x;
			lux[i].y += p->pos.y;
		}

		draw_polygon(&plux, GREEN);
	}
}


void draw_dorsal(dorsal_t* dorsal)
{
	for(int i=0; i<dorsal->num_panels; i++)
		draw_panel(&dorsal->panels[i]);

}

void draw_panels(panel_t* panels)
{
	for(panel_t* p=panels; p!=NULL; p=p->next) 
		draw_panel(p);
}

/* Drawing primitives */
cairo_t* init_cairo() {

    cairo_surface_t *surface;
    cairo_t *cr;
   
    surface = cairo_image_surface_create(CAIRO_FORMAT_ARGB32, WIDTH, HEIGHT);
    cr = cairo_create(surface);

    // Set background color
    cairo_set_source_rgb(cr, 1.0, 1.0, 1.0); // White
    cairo_paint(cr);

    // Set drawing color
    cairo_set_source_rgb(cr, 0.0, 0.0, 0.0); // Black

    return cr;
}

void init_canvas(transform_t trans)
{
	_canvas.cr = init_cairo();
	_canvas.trans = trans;
}

void draw_polygon(polygon_t* p, colour_t col) 
{

	cairo_t* cr = _canvas.cr;
	transform_t trsf = _canvas.trans;
	int i;

	cairo_set_source_rgb(cr, col.red, col.green, col.blue);
    cairo_move_to(cr, 
			p->poly[0].x*trsf.scale.x + trsf.origin.x, 
			p->poly[0].y*trsf.scale.y + trsf.origin.y);

    for (i = 1; i < p->len; i++) 
        cairo_line_to(cr, 
			p->poly[i].x*trsf.scale.x + trsf.origin.x, 
			p->poly[i].y*trsf.scale.y + trsf.origin.y); 

    //cairo_close_path(cr);
    cairo_stroke(cr);
}


void draw_box(box_t* box, colour_t col)
{
polygon_t pgon;
point_t points[5];

	points[0] = (point_t){box->xmin, box->ymin};
	points[1] = (point_t){box->xmin, box->ymax};
	points[2] = (point_t){box->xmax, box->ymax};
	points[3] = (point_t){box->xmax, box->ymin};
	points[4] = points[0];

	pgon.len = 5;
	pgon.poly = (point_t*)points;

	draw_polygon(&pgon, col);
}

void draw_point(point_t point)
{
box_t box = box_point(point, 10);

	draw_box(&box, RED);	
}

void save_png(char* filename)
{
	cairo_t* cr = _canvas.cr;
	cairo_surface_t* surface = cairo_get_target(cr);
    cairo_surface_write_to_png(surface, filename);
}

void print_text(char* text, int line)
{
	cairo_t* cr = _canvas.cr;
    cairo_set_source_rgb(cr, 0.0, 0.0, 0.0); // Black
	cairo_move_to(cr, 
			TEXT_OFFS_X, 
			TEXT_OFFS_Y + line*LINE_HEIGHT);
	cairo_show_text(cr, text);
	cairo_stroke(cr);
}

