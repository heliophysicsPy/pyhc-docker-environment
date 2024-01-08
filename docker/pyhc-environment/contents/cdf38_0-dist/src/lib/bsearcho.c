#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "cdf.h"

void RangeSearchForEPOCH (double *, int, int, double, double, int *);
void RangeSearchForEPOCH16 (double *, int, int, double *, double *, int *);
void RangeSearchForTT2000 (long long *, int, int, long long, long long, int *);

void RangeSearchForEPOCH (double *array, int first, int last, double start,
                          double stop, int *elements) {
   int total, middle;
   int beginning, ending;

   total = last - first + 1;
   if (start > stop || start > *(array+total-1) || stop < *array) {
     elements[0] = elements[1] = -1;
     return;
   }
   if (*array >= start) beginning = 0;
   else {
     middle = (first+last)/2;
     while (first <= last) {
       if (*(array+middle) > start) {
         last = middle - 1;
         if ((last-first) <= 1) {
           if (*(array+last) < start) {
             beginning = middle;
             break;
           }
         }
       } else if (*(array+middle) < start) {
         first = middle + 1;
         if ((last-first) <= 1) {
           if (*(array+first) > start) {
             beginning = first;
             break;
           }
         }
       } else {
         beginning = middle;
         break;
       }
       middle = (first + last)/2;
     }
   }
  
   if (*(array+total-1) <= stop)
     ending = total-1;
   else {
     first = beginning;
     last = total - 1;
     middle = (first+last)/2;
     while (first <= last) {
       if (*(array+middle) < stop) {
         first = middle + 1;
         if ((last-first) <= 1) {
           if (*(array+first) > stop) {
             ending = middle;
             break;
           }
         }
       } else if (*(array+middle) > stop) {
         last = middle - 1;
         if ((last-first) <= 1) {
           if (*(array+last) < stop) {
           ending = last;
           break;
           }
         }
       } else {
         //printf("%d found at location %d.\n", stop, middle);
         ending = middle;
         break;
       }
       middle = (first + last)/2;
     }
   }
   if (beginning > ending) {
     beginning = ending = -1;
   }
   elements[0] = beginning;
   elements[1] = ending;
}

void RangeSearchForEPOCH16 (double *array, int first, int last, double *start,
                            double *stop, int *elements) {
   int total, middle;
   int beginning, ending;

   total = last - first + 1;
   if (*start > *stop || (*start == *stop && *(start+1) > *(stop+1)) ||
       *start > *(array+2*total-2) || *stop < *array ||
       (*stop == *array && *(stop+1) < *(array+1)) ||
       (*start == *(array+2*total-2) && *(start+1) > *(array+2*total-1))) {
     elements[0] = elements[1] = -1;
     return;
   }
   if (*start < *array || (*start == *array && *(start+1) <= *(array+1)))
     beginning = 0;
   else {
     middle = (first+last)/2;
     while (first <= last) {
       if (*(array+2*middle) > *start ||
           (*(array+2*middle) == *start && *(array+2*middle+1) > *(start+1))) {
         last = middle - 1;
         if ((last-first) <= 1) {
           if (*(array+2*last) < *start ||
               (*(array+2*last) == *start && *(array+2*last+1) < *(start+1))) {
             beginning = middle;
             break;
           }
         }
       } else if (*(array+2*middle) < *start ||
                  (*(array+2*middle) == *start &&
                   *(array+2*middle+1) < *(start+1))) {
           first = middle + 1;
           if ((last-first) <= 1) {
             if (*(array+2*first) > *start ||
                 (*(array+2*first) == *start &&
                  *(array+2*first+1) > *(start+1))) {
               beginning = first;
               break;
             }
           }
       } else {
         beginning = middle;
         break;
       }
       middle = (first + last)/2;
     }
   }
  
   if (*(array+2*total-2) < *stop ||
       (*(array+2*total-2) == *stop && *(array+2*total-1) < *(stop+1)))
     ending = total-1;
   else {
     first = beginning;
     last = total - 1;
     middle = (first+last)/2;
     while (first <= last) {
       if (*(array+2*middle) < *stop ||
           (*(array+2*middle) == *stop && *(array+2*middle+1) < *(stop+1))) {
         first = middle + 1;
         if ((last-first) <= 1) {
           if (*(array+2*first) > *stop ||
               (*(array+2*first) == *stop && *(array+2*first+1) > *(stop+1))) {
             ending = middle;
             break;
           }
         }
       } else if (*(array+2*middle) > *stop ||
                  (*(array+2*middle) == *stop &&
                   *(array+2*middle+1) > *(stop+1))) {
         last = middle - 1;
         if ((last-first) <= 1) {
           if (*(array+2*last) < *stop ||
               (*(array+2*last) == *stop && *(array+2*last+1) < *(stop+1))) {
             ending = last;
             break;
           }
         }
       } else {
         //printf("%d found at location %d.\n", stop, middle);
         ending = middle;
         break;
       }
       middle = (first + last)/2;
     }
   }
   if (beginning > ending) {
     beginning = ending = -1;
   }
   elements[0] = beginning;
   elements[1] = ending;
}

void RangeSearchForTT2000 (long long *array, int first, int last, long long start,
                           long long stop, int *elements) {
   int total, middle;
   int beginning, ending;

   total = last - first + 1;
   if (start > stop || stop < *array || start > *(array+total-1)) {
     elements[0] = elements[1] = -1;
     return;
   }
   if (*array >= start) 
     beginning = 0;
   else {
     middle = (first+last)/2;
     while (first <= last) {
       if (*(array+middle) > start) {
         last = middle - 1;
         if ((last-first) <= 1) {
           if (*(array+last) < start) {
             beginning = middle;
             break;
           }
         }
       } else if (*(array+middle) < start) {
         first = middle + 1;
         if ((last-first) <= 1) {
           if (*(array+first) > start) {
             beginning = first;
             break;
           }
         }
       } else {
         beginning = middle;
         break;
       }
       middle = (first + last)/2;
     }
   }
  
   if (*(array+total-1) <= stop)
     ending = total-1;
   else {
     first = beginning;
     last = total - 1;
     middle = (first+last)/2;
     while (first <= last) {
       if (*(array+middle) < stop) {
         first = middle + 1;
         if ((last-first) <= 1) {
           if (*(array+first) > stop) {
             ending = middle;
             break;
           }
         }
       } else if (*(array+middle) > stop) {
         last = middle - 1;
         if ((last-first) <= 1) {
           if (*(array+last) < stop) {
             ending = last;
             break;
           }
         }
       } else {
         //printf("%d found at location %d.\n", stop, middle);
         ending = middle;
         break;
       }
       middle = (first + last)/2;
     }
   }
   if (beginning > ending) {
     beginning = ending = -1;
   }
   elements[0] = beginning;
   elements[1] = ending;
}

int main() {
   int first, last, total, middle;
   int beginning, ending;
   double array[] = {1,3,5,7,9,11,13,15,17,19};
   long long startl, stopl, array2[] = {1,3,5,7,9,11,13,15,17,19};
   double array3[] = {1,3,5,7,9,11,13,15,17,19,1,3,5,7,9,11,13,15,17,19};
   double start, stop, startd[2], stopd[2];
   char buf[81];
   int i, elements[2];

   total = 10;
   array[0] = 1;
   for (i=0;i<total;++i) {
     int val = rand();
     array[i] = (i==0?1:array[i-1]) + ((double)val)/RAND_MAX * 10;
     array2[i] = (long long) array[i];
     printf("%d:%g ",i,array[i]);
   }
   printf("\n");
   for (i=0;i<total;++i) {
     array2[i] = (long long) array[i];
     array3[2*i] = (long) (array[i]);
     printf("%d:%lld ",i,array2[i]);
   }
   printf("\n");
printf("\nenter start and end values:\n");
while (fgets(buf, sizeof(buf), stdin ) != NULL) {
if (sscanf(buf, "%lg %lg", &start, &stop) == 2) {
   first = 0;
   last = total - 1;
   RangeSearchForEPOCH(array, first, last, start, stop, elements);
   printf("%f and %f @ beginning=%d ending=%d\n",start, stop, elements[0], elements[1]);
   startl = (long long) start;
   stopl = (long long) stop;
   RangeSearchForTT2000(array2, first, last, startl, stopl, elements);
   printf("%lld and %lld @ beginning=%d ending=%d\n",startl, stopl, elements[0], elements[1]);
   startd[0] = (long) start;
   stopd[0] = (long) stop;
   RangeSearchForEPOCH16(array3, first, last, startd, stopd, elements);
   printf("%f and %f @ beginning=%d ending=%d\n",*startd, *stopd, elements[0], elements[1]);
}
else
  break;
}
   exit(1);

}

