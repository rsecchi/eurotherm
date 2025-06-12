#ifndef PLANNER_H
#define PLANNER_H
#include "engine.h"

/* 
 * The flags in iso_flgs describe 
 * the dihedral transformation (D8) around (x,y)
 *
 * where bit2 represents the reflection, and bit1:0 
 * one of the four 90-degree rotation.
 *
 * In Leonardo-2 panels are always symmetric
 * so the reflection bit is always zero.
 *
 */ 

typedef struct _pnl
{
	ptype type;
	double x, y;
	uint32_t iso_flgs;
	uint32_t dorsal_row;
	struct _pnl* next;
} pnl_t;


pnl_t* planner(room_t*, config_t*);
void free_list(pnl_t*);
void set_one_direction(int);

#endif
