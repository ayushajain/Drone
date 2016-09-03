/*
Copyright (C) 2015 3D Robotics

Permission is hereby granted, free of charge, to any
person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the
Software without restriction, including without
limitation the rights to use, copy, modify, merge,
publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software
is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice
shall be included in all copies or substantial portions
of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF
ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR
IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
*/

// Based on https://linuxtv.org/downloads/v4l-dvb-apis/capture-example.html

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <stdint.h>

#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/time.h>
#include <sys/mman.h>
#include <sys/ioctl.h>

#include <linux/videodev2.h>

#include "solocam.h"

#define CLEAR(x) memset(&(x), 0, sizeof(x))
#define MAX_BUFFERS 8

struct solocam_ctx {
  int fd;
  unsigned num_buffers;
  solocam_buf buffers[MAX_BUFFERS];
  struct v4l2_format fmt;
};

static void logerr(const char *s) {
    fprintf(stderr, "%s error %d, %s\n", s, errno, strerror(errno));
}

static int xioctl(int fh, int request, void *arg) {
  int r;

  do {
    r = ioctl(fh, request, arg);
  } while (-1 == r && EINTR == errno);

  return r;
}

int solocam_open_hdmi(struct solocam_ctx** ctxp) {
  struct stat st;
  
  const char* dev_name = "/dev/video0";

  if (-1 == stat(dev_name, &st)) {
    fprintf(stderr, "Cannot identify '%s': %d, %s\n",
             dev_name, errno, strerror(errno));
    return EXIT_FAILURE;
  }

  if (!S_ISCHR(st.st_mode)) {
    fprintf(stderr, "%s is no device\n", dev_name);
    return EXIT_FAILURE;
  }

  int fd = open(dev_name, O_RDWR /* required */ /*| O_NONBLOCK*/, 0);

  if (-1 == fd) {
    fprintf(stderr, "Cannot open '%s': %d, %s\n",
             dev_name, errno, strerror(errno));
    return EXIT_FAILURE;
  }
  
  struct v4l2_capability cap;

  if (-1 == xioctl(fd, VIDIOC_QUERYCAP, &cap)) {
     if (EINVAL == errno) {
       fprintf(stderr, "%s is no V4L2 device\n",
                dev_name);
       exit(EXIT_FAILURE);
     } else {
       logerr("VIDIOC_QUERYCAP");
       return errno;
     }
  }

  if (!(cap.capabilities & V4L2_CAP_VIDEO_CAPTURE)) {
    fprintf(stderr, "%s is no video capture device\n",
            dev_name);
    return EXIT_FAILURE;
  }
  
  if (!(cap.capabilities & V4L2_CAP_STREAMING)) {
    fprintf(stderr, "%s does not support streaming i/o\n",
             dev_name);
    return EXIT_FAILURE;
  }
  
  struct v4l2_cropcap cropcap;
  struct v4l2_crop crop;
  CLEAR(cropcap);

  cropcap.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;

  if (0 == xioctl(fd, VIDIOC_CROPCAP, &cropcap)) {
    crop.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    crop.c = cropcap.defrect; /* reset to default */

    if (-1 == xioctl(fd, VIDIOC_S_CROP, &crop)) {
        switch (errno) {
        case EINVAL:
                /* Cropping not supported. */
                break;
        default:
                /* Errors ignored. */
                break;
        }
    }
  } else {
          /* Errors ignored. */
  }
  
  int s_input = 1;
  if (-1 == xioctl(fd, VIDIOC_S_INPUT, &s_input)) {
    logerr("VIDIOC_S_INPUT");
    return errno;
  }
  
  solocam_ctx* ctx = calloc(1, sizeof(*ctx));
  ctx->fd = fd;
  *ctxp = ctx;
  
  return 0;
}

int solocam_crop(struct solocam_ctx* ctx, int x, int y, int width, int height) {
  struct v4l2_crop crop;
  CLEAR(crop);
  
  crop.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
  crop.c.left = x;
  crop.c.top = y;
  crop.c.width = width;
  crop.c.height = height;

  if (-1 == xioctl(ctx->fd, VIDIOC_S_CROP, &crop)) {
    logerr("VIDIOC_S_CROP");
    return errno;
  }
  
  return 0;
}

int solocam_get_size(struct solocam_ctx* ctx, int* widthp, int* heightp) {
  *widthp = ctx->fmt.fmt.pix.width;
  *heightp = ctx->fmt.fmt.pix.height;
  return 0;
}

/// Grayscale = Y plane of YUV420
int solocam_set_format_720p60_grayscale(struct solocam_ctx* ctx) {
  struct v4l2_streamparm streamparm;
  
  streamparm.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
  streamparm.parm.capture.capturemode = 4;
  streamparm.parm.capture.timeperframe.denominator = 60;
  streamparm.parm.capture.timeperframe.numerator = 1;
  
  if (-1 == xioctl(ctx->fd, VIDIOC_S_PARM, &streamparm)) {
    logerr("VIDIOC_S_PARM");
    return errno;
  }
 
  CLEAR(ctx->fmt);

  ctx->fmt.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
  ctx->fmt.fmt.pix.width       = 1920;
  ctx->fmt.fmt.pix.height      = 1080;
  ctx->fmt.fmt.pix.pixelformat = V4L2_PIX_FMT_YUV420;
  ctx->fmt.fmt.pix.field       = V4L2_FIELD_ANY;

  if (-1 == xioctl(ctx->fd, VIDIOC_S_FMT, &ctx->fmt)) {
    logerr("VIDIOC_S_FMT");
    return errno;
  }

/*
  if (-1 == xioctl(ctx->fd, VIDIOC_G_FMT, &ctx->fmt)){
    logerr("VIDIOC_G_FMT");
    return errno;
  }
*/

  /* Buggy driver paranoia. */
  int min = ctx->fmt.fmt.pix.width * 2;
  if (ctx->fmt.fmt.pix.bytesperline < min)
          ctx->fmt.fmt.pix.bytesperline = min;
  min = ctx->fmt.fmt.pix.bytesperline * ctx->fmt.fmt.pix.height;
  if (ctx->fmt.fmt.pix.sizeimage < min)
          ctx->fmt.fmt.pix.sizeimage = min;
          
  return 0;
}

int solocam_start(struct solocam_ctx* ctx) {
  struct v4l2_requestbuffers req;

  CLEAR(req);

  req.count = MAX_BUFFERS;
  req.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
  req.memory = V4L2_MEMORY_MMAP;

  if (-1 == xioctl(ctx->fd, VIDIOC_REQBUFS, &req)) {
    if (EINVAL == errno) {
      fprintf(stderr, "Device does not support memory mapping\n");
      return EXIT_FAILURE;
    } else {
      logerr("VIDIOC_REQBUFS");
      return errno;
    }
  }

  if (req.count < 2) {
    fprintf(stderr, "Insufficient buffer memory on device\n");
    return EXIT_FAILURE;
  }
  
  ctx->num_buffers = req.count;

  for (int n_buffers = 0; n_buffers < ctx->num_buffers; ++n_buffers) {
    struct v4l2_buffer buf;

    CLEAR(buf);

    buf.type        = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    buf.memory      = V4L2_MEMORY_MMAP;
    buf.index       = n_buffers;

    if (-1 == xioctl(ctx->fd, VIDIOC_QUERYBUF, &buf)) {
        logerr("VIDIOC_QUERYBUF");
        return errno;
    }

    ctx->buffers[n_buffers].id = n_buffers;
    ctx->buffers[n_buffers].length = buf.length;
    ctx->buffers[n_buffers].data =
            mmap(NULL,
                  buf.length,
                  PROT_READ | PROT_WRITE,
                  MAP_SHARED,
                  ctx->fd, buf.m.offset);

    if (MAP_FAILED == ctx->buffers[n_buffers].data) {
      logerr("mmap");
      return errno;
    }
  }
  
  
  for (int i = 0; i < ctx->num_buffers; ++i) {
    struct v4l2_buffer buf;

    CLEAR(buf);
    buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    buf.memory = V4L2_MEMORY_MMAP;
    buf.index = i;

    if (-1 == xioctl(ctx->fd, VIDIOC_QBUF, &buf)) {
      logerr("VIDIOC_QBUF (start)");
      return errno;
    }
  }
  unsigned type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
  if (-1 == xioctl(ctx->fd, VIDIOC_STREAMON, &type)) {
    logerr("VIDIOC_STREAMON");
    return errno;
  }
  
  return 0;
}

int solocam_stop(struct solocam_ctx* ctx) {
  enum v4l2_buf_type type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
  if (-1 == xioctl(ctx->fd, VIDIOC_STREAMOFF, &type)) {
    logerr("VIDIOC_STREAMOFF");
  }
  
  return 0;
}

int solocam_read_frame(struct solocam_ctx* ctx, solocam_buf** bufp) {
  struct v4l2_buffer buf;
  
  CLEAR(buf);

  buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
  buf.memory = V4L2_MEMORY_MMAP;

  if (-1 == xioctl(ctx->fd, VIDIOC_DQBUF, &buf)) {
    logerr("VIDIOC_DQBUF");
    return errno;
  }

  assert(buf.index < ctx->num_buffers);

  ctx->buffers[buf.index].used = buf.bytesused;
  *bufp = &ctx->buffers[buf.index];
  
  return 0;
}

int solocam_free_frame(struct solocam_ctx* ctx, solocam_buf* buf) {
  struct v4l2_buffer vbuf;
  
  vbuf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
  vbuf.memory = V4L2_MEMORY_MMAP;
  vbuf.index = buf->id;
  
  if (-1 == xioctl(ctx->fd, VIDIOC_QBUF, &vbuf)) {
    logerr("VIDIOC_QBUF (free)");
    return errno;
  }
  
  return 0;
}

int solocam_close(struct solocam_ctx* ctx) {
  close(ctx->fd);
  free(ctx);
  return 0;
}

