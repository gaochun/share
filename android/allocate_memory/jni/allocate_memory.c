#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#define MB (1024*1024)

void set_oom(char *oom_value);

int main(int argc, char *argv[]) {
	if (argc != 2) {
		perror("error input, please add the memory size you want to apply as a parameter!\n");
		exit(0);
	}
	int i;
	for (i = 0; i < strlen(argv[1]); i++) {
		if (!isdigit(argv[1][i])) {
			perror("error input: the memory size you input should be an integer(uint:M)\n");
			exit(0);
		}
	}

	//set the oom_adj value=-17 to prevent to be killed by lowmemkiller
	set_oom("-17");

	//allocate the memory: argv[1] MB
	int memory_size = atoi(argv[1]);
	printf("memory size: %d\n", memory_size);
	void *array = malloc(memory_size * MB);
	memset(array, 0, memory_size * MB);
	printf("%d MB memory has been allocated!\n", memory_size);
	printf("-------sleeping---------\n");
	pause();

	return 0;
}

void set_oom(char *oom_value) {
	//get the pid
	char oom_path[128];
	sprintf(oom_path, "/proc/%d/oom_adj", getpid());
	printf("oom_path:%s\n", oom_path);
	//open the oom_adj file in "w" mode
	FILE *fp;
	if ((fp = fopen(oom_path, "w")) == NULL) {
		perror("--------error--------\n");
		perror("The oom_adj file can't be opened!\n");
		exit(0);
	}
	//set the oom_adj value
	fwrite(oom_value, sizeof(char), strlen(oom_value), fp);
	fclose(fp);
}

