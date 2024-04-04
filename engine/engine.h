#ifndef ENGINE_H
#define ENGINE_H

#include "geometry.h"

#define LUX_WIDTH   100.
#define LUX_HEIGHT   20.
#define EDGE         10.

typedef enum {
	FULL,    // panel 200 x 120 cm
	HALF,    // panel 100 x 120 cm
	SPLIT,   // panel 200 x 60  cm
	QUARTER, // panel 100 x 60  cm
	LUX,     // lux panel  200 x 120 cm
	NUM_PANEL_T
} ptype;

typedef enum {
	UP, DOWN
} heading_t;

typedef struct{
	polygon_t walls;
	polygon_t* obstacles;
	int obs_num;
} room_t;

typedef struct{
	ptype type;
	point_t pos;
	heading_t heading;
	box_t pbox;
} panel_t;


int fit(panel_t* p, room_t* r);
int gap_is_okay(point_t *q, room_t* r);
void panel(panel_t* pp, ptype pt, point_t pos, heading_t ht);

void draw_room(canvas_t*, room_t*);
void draw_panel(canvas_t*, panel_t*);

#endif
