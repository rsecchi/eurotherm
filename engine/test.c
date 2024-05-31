#include "planner.h"
#include <stdio.h>

int main()
{

	pnl_t*list = make_list();
	printf("TESTING PLANNER\n");
	print(list);
	free_list(list);
}


