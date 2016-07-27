#include <stdint.h>
#include <stdlib.h>

struct solocam_ctx;
typedef struct solocam_ctx solocam_ctx;

typedef struct solocam_buf {
  int id;
  uint8_t *data;
  size_t length;
  size_t used;
} solocam_buf;

int solocam_open_hdmi(solocam_ctx** ctx);

int solocam_crop(solocam_ctx* ctx, int x, int y, int width, int height);
int solocam_get_size(solocam_ctx* ctx, int* widthp, int* heightp);

// YUV420, use Y plane for grayscale
int solocam_set_format_720p60_grayscale(solocam_ctx* ctx);

int solocam_start(solocam_ctx* ctx);
int solocam_stop(solocam_ctx* ctx);

int solocam_read_frame(solocam_ctx* ctx, solocam_buf** bufptr);
int solocam_free_frame(solocam_ctx* ctx, solocam_buf* ptr);

int solocam_close(solocam_ctx* ctx);