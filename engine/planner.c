#include "planner.h"
#include <stdio.h>
#include <stdlib.h>

pnl_t* make_list()
{
pnl_t* head = NULL, *q;

	for(int i=0; i<10; i++) {
		q = malloc(sizeof(pnl_t));
		q->next = head;
		q->type = rand() % NUM_PANEL_T;
		head = q;
	}

	return head;
}

void free_list(pnl_t* head)
{
pnl_t *p, *q;
	p=head;
	while(p!=NULL) {
		q = p->next;
		free(p);
		p = q;
	}
}

void print(pnl_t* head)
{

	for(pnl_t* p=head; p!=NULL; p=p->next) {
		printf("%s\n", panel_desc[p->type].name);
	}


}



