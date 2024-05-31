#ifndef PLANNER_H
#define PLANNER_H
#include "engine.h"

typedef struct _pnl
{
	ptype type;
	struct _pnl* next;
} pnl_t;


pnl_t* make_list();
void free_list(pnl_t*);
void print(pnl_t*);

#endif
