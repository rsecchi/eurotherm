#ifndef cairo_drawing_h
#define cairo_drawing_h

#include <cairo/cairo.h>

#include "engine.h"

/* libcairo drawing support */
typedef struct {
	point_t origin;
	point_t scale;
} transform_t;

typedef struct {
	double red, green, blue;
} colour_t;

typedef struct {
	cairo_t* cr;
	transform_t trans;
} canvas_t;


extern canvas_t _canvas;

// Drawing
#define WIDTH  640
#define HEIGHT 480

#define TEXT_OFFS_X    10
#define TEXT_OFFS_Y    20
#define LINE_HEIGHT    10

#define RED    (colour_t){1., 0., 0.}
#define GREEN  (colour_t){0., 1., 0.}
#define BLUE   (colour_t){0., 0., 1.}
#define YELLOW (colour_t){1., 1., 0.}
#define ORANGE (colour_t){1., .5, 0.}
#define BLACK  (colour_t){0., 0., 0.}

void init_canvas(transform_t trans);

void draw_room(room_t *rp);
void draw_rect(box_t* box, colour_t col);
void draw_panel(panel_t* p);
void draw_dorsal(dorsal_t* dorsal);
void draw_panels(panel_t* panels);

void draw_polygon(polygon_t* poly, colour_t col);
void draw_box(box_t* box, colour_t col);
void draw_point(point_t point);

void print_text(char* text, int line);

void save_png(char* filename);

#endif

