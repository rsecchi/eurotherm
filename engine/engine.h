#ifndef ENGINE_H
#define ENGINE_H
#include <stdint.h>
#include "geometry.h"

#define LUX_WIDTH           100.
#define LUX_HEIGHT           20.
#define EDGE                 10.
#define MAX_RAILS           256
#define MAX_LINES          2048
#define MAX_DORSAL_PANELS    64
#define INTER_RAIL_GAP       50.
#define INTER_LINE_GAP       10.
#define DIST_FROM_WALLS      18.

extern canvas_t* __debug_canvas;

typedef enum {
	FULL,    // panel 200 x 120 cm
	LUX,     // lux panel  200 x 120 cm
	SPLIT,   // panel 200 x 60  cm
	HALF,    // panel 100 x 120 cm
	QUARTER, // panel 100 x 60  cm
	NUM_PANEL_T
} ptype;

typedef enum {UP, DOWN} heading_t;
typedef enum {WIDE, NARROW} dorsal_width_t;

typedef struct{
	double width;
	double height; 
	uint32_t score;
	uint32_t prev;
	char name[16];
} panel_desc_t;

extern panel_desc_t panel_desc[]; 

typedef struct{
	polygon_t walls;
	polygon_t* obstacles;
	int obs_num;
	box_t box;
} room_t;

typedef struct __panel {
	ptype type;
	point_t pos;
	heading_t heading;
	box_t pbox;
	uint32_t score;
	struct __panel* next;
} panel_t;

typedef struct {
	point_t offset;
	heading_t heading;
	dorsal_width_t width;
	panel_t panels[MAX_DORSAL_PANELS];
	int num_panels;
	uint32_t score;
} dorsal_t;

int fit(panel_t*, room_t*);
int gap_ok(panel_t*, room_t*);

uint32_t make_dorsal(room_t*, dorsal_t*);
uint32_t scanline(room_t*);
void panel(panel_t*, ptype, point_t, heading_t);


void draw_room(canvas_t*, room_t*);
void draw_panel(canvas_t*, panel_t*);
void draw_panels(canvas_t*, dorsal_t*);

#endif
