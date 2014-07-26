/* -*- Mode: C -*- */

/*
 *  Author: Sam Rushing <rushing@nightmare.com>
 *
 */

#include "Python.h"

#define LITTLE_ENCODE_WORD(x,s)                 \
  do {                                          \
    (s)[0] = x & 0xff; x >>= 8;                 \
    (s)[1] = x & 0xff;                          \
  } while (0)

#define LITTLE_ENCODE_LONG(x,s)                 \
  do {                                          \
    (s)[0] = x & 0xff; x >>= 8;                 \
    (s)[1] = x & 0xff; x >>= 8;                 \
    (s)[2] = x & 0xff; x >>= 8;                 \
    (s)[3] = x & 0xff;                          \
  } while (0)

#define LITTLE_DECODE_WORD(x,s)                 \
  do {                                          \
    x = (s)[1] << 8 | (s)[0];                   \
  } while (0)

#define LITTLE_DECODE_LONG(x,s)                             \
  do {                                                      \
    x = (s)[3] << 24 | (s)[2] << 16 | (s)[1] << 8 | (s)[0]; \
  } while (0)
     
#define BIG_ENCODE_WORD(x,s)                    \
  do {                                          \
    (s)[1] = x & 0xff; x >>= 8;                 \
    (s)[0] = x & 0xff;                          \
  } while (0)

#define BIG_ENCODE_LONG(x,s)                    \
  do {                                          \
    (s)[3] = x & 0xff; x >>= 8;                 \
    (s)[2] = x & 0xff; x >>= 8;                 \
    (s)[1] = x & 0xff; x >>= 8;                 \
    (s)[0] = x & 0xff;                          \
  } while (0)

#define BIG_DECODE_WORD(x,s)                    \
  do {                                          \
    x = (s)[0] << 8 | (s)[1];                   \
  } while (0)

#define BIG_DECODE_LONG(x,s)                                \
  do {                                                      \
    x = (s)[0] << 24 | (s)[1] << 16 | (s)[2] << 8 | (s)[3]; \
  } while (0)

/* Encoding floating-point values is a bit more complicated */

/* Assumptions:
 * float is 4-byte IEEE
 * double is 8-byte IEEE
 * machine is either little or big-endian
 */

#define SWAP(s,a,b)                             \
  do {                                          \
    unsigned char temp = s[a];                  \
    s[a] = s[b];                                \
    s[b] = temp;                                \
  } while (0)

#define NATIVE_ENCODE_FLOAT(x,s)                \
  do {                                          \
    (*(float *)(s)) = x;                        \
  } while (0)


#define ALIEN_ENCODE_FLOAT(x,s)                 \
  do {                                          \
    (*(float *)(s)) = x;                        \
    SWAP (s,0,3); SWAP(s,1,2);                  \
  } while (0)

#define LITTLE_ENCODE_FLOAT(x,s)                \
  do {                                          \
    if (endian) {                               \
      ALIEN_ENCODE_FLOAT (x,s);                 \
    } else {                                    \
      NATIVE_ENCODE_FLOAT (x,s);                \
    }                                           \
  } while (0)

#define BIG_ENCODE_FLOAT(x,s)                   \
  do {                                          \
    if (endian) {                               \
      NATIVE_ENCODE_FLOAT (x,s);                \
    } else {                                    \
      ALIEN_ENCODE_FLOAT (x,s);                 \
    }                                           \
  } while (0)

#define NATIVE_ENCODE_DOUBLE(x,s)               \
  do {                                          \
    (*(double *)(s)) = x;                       \
  } while (0)


#define ALIEN_ENCODE_DOUBLE(x,s)                \
  do {                                          \
    (*(double *)(s)) = x;                       \
    SWAP (s,0,7); SWAP(s,1,6);                  \
    SWAP (s,2,5); SWAP(s,3,4);                  \
  } while (0)

#define LITTLE_ENCODE_DOUBLE(x,s)               \
  do {                                          \
    if (endian) {                               \
      ALIEN_ENCODE_DOUBLE (x,s);                \
    } else {                                    \
      NATIVE_ENCODE_DOUBLE (x,s);               \
    }                                           \
  } while (0)

#define BIG_ENCODE_DOUBLE(x,s)                  \
  do {                                          \
    if (endian) {                               \
      NATIVE_ENCODE_DOUBLE (x,s);               \
    } else {                                    \
      ALIEN_ENCODE_DOUBLE (x,s);                \
    }                                           \
  } while (0)


#define NATIVE_DECODE_FLOAT(x,s)                \
  do {                                          \
    x = (*(float *)(s));                        \
  } while (0)


#define ALIEN_DECODE_FLOAT(x,s)                 \
  do {                                          \
    SWAP ((s),0,3); SWAP((s),1,2);              \
    x = (*(float *)(s));                        \
    SWAP ((s),0,3); SWAP((s),1,2);              \
  } while (0)

#define NATIVE_DECODE_DOUBLE(x,s)               \
  do {                                          \
    x = (*(double *)(s));                       \
  } while (0)


#define ALIEN_DECODE_DOUBLE(x,s)                \
  do {                                          \
    SWAP (s,0,7); SWAP(s,1,6);                  \
    SWAP (s,2,5); SWAP(s,3,4);                  \
    x = (*(double *)(s));                       \
    SWAP (s,0,7); SWAP(s,1,6);                  \
    SWAP (s,2,5); SWAP(s,3,4);                  \
  } while (0)

#define LITTLE_DECODE_FLOAT(x,s)                \
  do {                                          \
    if (endian) {                               \
      ALIEN_DECODE_FLOAT (x,(s));               \
    } else {                                    \
      NATIVE_DECODE_FLOAT (x,(s));              \
    }                                           \
  } while (0)

#define LITTLE_DECODE_DOUBLE(x,s)               \
  do {                                          \
    if (endian) {                               \
      ALIEN_DECODE_DOUBLE (x,(s));              \
    } else {                                    \
      NATIVE_DECODE_DOUBLE (x,(s));             \
    }                                           \
  } while (0)

#define BIG_DECODE_FLOAT(x,s)                   \
  do {                                          \
    if (endian) {                               \
      NATIVE_DECODE_FLOAT (x,(s));              \
    } else {                                    \
      ALIEN_DECODE_FLOAT (x,(s));               \
    }                                           \
  } while (0)

#define BIG_DECODE_DOUBLE(x,s)                  \
  do {                                          \
    if (endian) {                               \
      NATIVE_DECODE_DOUBLE (x,(s));             \
    } else {                                    \
      ALIEN_DECODE_DOUBLE (x,(s));              \
    }                                           \
  } while (0)


static int endian = 0;          /* 0 == little; 1 == big */

static int
get_bit_length_list (PyObject * bit_lengths, char * format, int pos)
{
  char ch;
  int num = 0;
  int flag = 1;

  while (flag) {
    ch = format[pos++];
    switch (ch) {
    case '\000':
      PyErr_SetString (PyExc_ValueError, "unterminated bitfield description");
      return -1;
      break;
    case ')':
      PyList_Append (bit_lengths, PyInt_FromLong (num));
      flag = 0;
      break;
    case ' ':
      PyList_Append (bit_lengths, PyInt_FromLong (num));
      num = 0;
      break;
    default: {
        if ((ch >= '0') && (ch <= '9')) {
          num = (num * 10) + (ch-'0');
        } else {
          PyErr_SetString (PyExc_ValueError, "bogus character in bitfield description");
          Py_DECREF (bit_lengths);
          return -1;
        }
      }
    }
  }
  return pos;
}


static PyObject *
pack_bitfield (PyObject * bit_lengths, PyObject * data, int data_pos)
{
  int i;
  int bit_pos = 0;
  unsigned char byte = 0;

  /* how many bytes? */
  int num = PyList_Size (bit_lengths);
  int total_bits = 0;

  if ((PyTuple_Size (data) + data_pos) < num) {
    PyErr_SetString (PyExc_ValueError, "not enough data for bitfields");
    return NULL;
  }

  for (i=0; i < num; i++) {
    total_bits += PyInt_AsLong (PyList_GetItem (bit_lengths, i));
  }

  if ((total_bits % 8) != 0) {
    PyErr_SetString (PyExc_ValueError, "bitfields not octet-aligned");
    return NULL;
  } else {
    PyObject * result = PyString_FromString ("");
    for (i=0; i < num; i++) {
      int num_bits = PyInt_AsLong (PyList_GetItem  (bit_lengths, i));
      int value    = PyInt_AsLong (PyTuple_GetItem (data, i+data_pos));
      if (value >= (1 << num_bits)) {
        PyErr_SetString (PyExc_ValueError, "number too big for specified number of bits");
        return NULL;
      } else {
        while (num_bits) {
          if (bit_pos == 8) {
            /* start a new output byte */
            PyString_ConcatAndDel (&result, PyString_FromStringAndSize ((char*)&byte, 1));
            byte = 0;
            bit_pos = 0;
          }
          num_bits = num_bits - 1;
          byte <<= 1;
          if (value & (1<<num_bits)) {
            byte |= 1;
          }
          bit_pos += 1;
        }
      }
    }
    PyString_ConcatAndDel (&result, PyString_FromStringAndSize ((char*)&byte, 1));
    return result;
  }
}

static
int
unpack_bitfield (
  PyObject * bit_length_list,
  PyObject * result_list,
  unsigned char * data,
  int data_pos,
  int data_len
  )
{
  int i;
  /* how many bytes? */
  int num = PyList_Size (bit_length_list);
  int total_bits = 0;
  
  for (i=0; i < num; i++) {
    total_bits += PyInt_AsLong (PyList_GetItem (bit_length_list, i));
  }

  if ((total_bits % 8) != 0) {
    PyErr_SetString (PyExc_ValueError, "bitfields not octet-aligned");
    return -1;
  } else {
    if ((data_pos + (total_bits/8)) > data_len) {
      PyErr_SetString (PyExc_ValueError, "not enough data for bitfields");
      return -1;
    } else {
      int bit_pos = 0;
      int i;

      for (i=0; i < num; i++) {
        int num_bits = PyInt_AsLong (PyList_GetItem (bit_length_list, i));
        int j;
        int x=0;

        for (j=0; j < num_bits; j++) {
          x = (x<<1) | ((data[data_pos] & (1<<(7-bit_pos))) ? 1 : 0);
          bit_pos++;
          if (bit_pos == 8) {
            bit_pos = 0;
            data_pos++;
          }
        }
        PyList_Append (result_list, PyInt_FromLong (x));
      }
      return (data_pos);
    }
  }
}

static
PyObject  *
pack (PyObject * self, PyObject * arg_list)
{
  char * format;
  int format_len;
  PyObject * args;
  PyObject * functions = NULL;

  if (!PyArg_ParseTuple (arg_list,
                         "s#O!|O!",
                         &format,
                         &format_len,
                         &PyTuple_Type,
                         &args,
                         &PyDict_Type,
                         &functions
                         )) {
    return NULL;
  } else {
    PyObject * result = PyString_FromString ("");
    PyObject * value;
    int argnum = 0;
    char ch;
    int num = 0;
    int i;
    char byte_order = format[0];

    /* check for a specified byte order */
    switch (byte_order) {
    case 'L':
    case 'B':
      i = 1;
      break;
    case 'N':
      /* Native byte order */
      /* <endian> is computed when this module is initialized */
      byte_order = endian ? 'B' : 'L';
      i = 1;
      break;
    default:
      /* default to native if not specified */
      byte_order = endian ? 'B' : 'L';
      i = 0;
      break;
    }
    
    while (ch = format[i]) {
      char * spec_start = format+i;
      i++;

      if ((ch >= '0') && (ch <= '9')) {
        num = (num * 10) + (ch - '0');
      } else {
        unsigned char s[8] = {0,0,0,0,0,0,0,0};

        if (ch != 'x') {
          value = PyTuple_GetItem (args, argnum++);
          if ((!value)) {
            PyErr_SetString (PyExc_ValueError, "not enough arguments for pack");
            Py_DECREF (result);
            return NULL;
          }         
        } else {
          /* kludge: when passing an argument tuple for a multiplied pad char ('4x'),
           * there really _isn't_ one.  Instead of creating an empty bogus tuple,
           * we will just pass in <args>... it won't used, but will keep BuildValue
           * from hurling
           */
          value = args;
        }

        /* handle multipliers by recursing */
        if (num > 0) {
          PyObject * spec;
          PyObject * full_spec;
          char * eos;
          int spec_len;
          /* build a new format string */
          /* <BYTE_ORDER> + <n>*<format> */
          switch (ch) {
          case 'b': case 'h': case 'l':
          case 'c': case 'd': case 'f':
          case 'x':
            spec = PyString_FromStringAndSize (&ch, 1);
            spec_len = 1;
            break;
          case '(':
            eos = strchr (spec_start, ')');
            if ((!eos) || (eos-format > format_len)) {
              PyErr_SetString (PyExc_ValueError, "unterminated bit field");
              Py_DECREF (result);
              return NULL;
            } else {
              spec_len = (eos-spec_start) + 1;
              spec = PyString_FromStringAndSize (spec_start, spec_len);
            }
            break;
          case '[':
            eos = strchr (spec_start, ']');
            if ((!eos) || (eos-format > format_len)) {
              PyErr_SetString (PyExc_ValueError, "unterminated bit field");
              Py_DECREF (result);
              return NULL;
            } else {
              spec_len = (eos-spec_start) + 1;
              spec = PyString_FromStringAndSize (spec_start, spec_len);
            }
            break;
          }
          /* make a one-character byte order spec */
          full_spec = PyString_FromStringAndSize (&byte_order, 1);
          /* now repeat the spec string */
          PyString_ConcatAndDel (&full_spec, PySequence_Repeat (spec, num));
          Py_DECREF (spec);
          /* recurse */
          {
            PyObject * packed;
            PyObject * args;
            if (functions) {
              args = Py_BuildValue ("OOO", full_spec, value, functions);
            } else {
              args = Py_BuildValue ("OO", full_spec, value);
            }
            packed = pack (NULL, args);
            Py_DECREF (args);
            if (!packed) {
              return NULL;
            } else {
              PyString_ConcatAndDel (&result, packed);
              Py_DECREF (full_spec);
              i += spec_len - 1;
              num = 0;
            }
          }
        } else {
          switch (ch) {
            
            /* integer types */
            
          case 'b': case 'h': case 'l':
            if (!PyInt_Check (value)) {
              PyErr_SetString (PyExc_ValueError, "bad argument type to pack");
              Py_DECREF (result);
              return NULL;
            } else {
              int x = PyInt_AsLong (value);
              int size=0;

              /* FIXME: should do range checks */
              switch (ch) {
              case 'b':
                size = 1;
                s[0] = x;
                break;
              case 'h':
                size = 2;
                switch (byte_order) {
                case 'L':
                  LITTLE_ENCODE_WORD (x,s);
                  break;
                case 'B':
                  BIG_ENCODE_WORD (x,s);
                  break;
                }
                break;
              case 'l':
                size = 4;
                switch (byte_order) {
                case 'L':
                  LITTLE_ENCODE_LONG (x,s);
                  break;
                case 'B':
                  BIG_ENCODE_LONG (x,s);
                  break;
                }
                break;
              }
              PyString_ConcatAndDel (&result, PyString_FromStringAndSize ((char *)s,size));
            }
            break;

            /* floating-point types */

          case 'f':
            if (!PyFloat_Check (value)) {
              PyErr_SetString (PyExc_ValueError, "bad argument type to pack");
              Py_DECREF (result);
              return NULL;
            } else {
              float x = (float) PyFloat_AsDouble (value);
              switch (byte_order) {
              case 'L':
                LITTLE_ENCODE_FLOAT (x,s);
                break;
              case 'B':
                BIG_ENCODE_FLOAT (x,s);
                break;
              }
              PyString_ConcatAndDel (&result, PyString_FromStringAndSize ((char *)s,4));
            }
            break;
              
          case 'd':
            if (!PyFloat_Check (value)) {
              PyErr_SetString (PyExc_ValueError, "bad argument type to pack");
              Py_DECREF (result);
              return NULL;
            } else {
              double x = PyFloat_AsDouble (value);
              switch (byte_order) {
              case 'L':
                LITTLE_ENCODE_DOUBLE (x,s);
                break;
              case 'B':
                BIG_ENCODE_DOUBLE (x,s);
                break;
              }
              PyString_ConcatAndDel (&result, PyString_FromStringAndSize ((const char *)s, 8));
            }
            break;

            /* character type */

          case 'c':
            if ((!PyString_Check (value)) || (PyString_Size (value) != 1)) {
              PyErr_SetString (PyExc_ValueError, "bad argument type to pack");
              Py_DECREF (result);
              return NULL;
            } else {
              /* careful... don't want to DECREF <value> */
              PyString_Concat (&result, value);
            }
            break;
              
            /* pad byte */

          case 'x':
            /* pad with a NULL byte */
            PyString_ConcatAndDel (&result, PyString_FromStringAndSize ("\000", 1));
            break;

          case '(':

            /* bitfield */

            {
              PyObject * bit_length_list = PyList_New (0);
              int new_pos = get_bit_length_list (bit_length_list, format, i);
              if (new_pos == -1) {
                /* get_bit_length_list will set the error */
                Py_DECREF (bit_length_list);
                Py_DECREF (result);
                return NULL;
              } else {
                PyObject * bits = pack_bitfield (bit_length_list, args, argnum-1);
                if (!bits) {
                  return NULL;
                } else {
                  PyString_ConcatAndDel (&result, bits);
                  i = new_pos;
                  argnum = argnum + PyList_Size (bit_length_list) - 1;
                }
                Py_DECREF (bit_length_list);
              }
            }
          break;
          
          case '[':
            {
              /* user function */
            
              char * eos = strchr (format+i, ']');
              if (!eos) {
                Py_DECREF (result);
                PyErr_SetString (PyExc_ValueError, "unterminated user function name");
                return NULL;
              } else {
                PyObject * key = PyString_FromStringAndSize (format+i, eos-(format+i));
                PyObject * fun;
                if ((!functions) || (!(fun = PyDict_GetItem (functions, key)))) {
                  PyErr_SetString (PyExc_ValueError, "unknown user function");
                  Py_DECREF (key);
                  Py_DECREF (result);
                  return NULL;
                } else {
                  Py_DECREF (key);
                  if (!PyCallable_Check (fun)) {
                    PyErr_SetString (PyExc_ValueError, "not a callable function");
                    Py_DECREF (result);
                    return NULL;
                  } else {
                    PyObject * sub;
                    PyObject * t = Py_BuildValue ("(O)", value);
                    sub = PyEval_CallObject (fun, t);
                    Py_DECREF (t);
                    if ((!sub) || (!PyString_Check (sub))) {
                      PyErr_SetString (PyExc_ValueError, "user function did not return a string");
                      Py_XDECREF (sub);
                      Py_DECREF (result);
                      return NULL;
                    } else {
                      i = (eos-format)+1;
                      PyString_ConcatAndDel (&result, sub);
                    }
                  }
                }
              }
            }
          break;

          default:
            PyErr_SetString (PyExc_ValueError, "unknown format character");
            Py_DECREF (result);
            return NULL;
            break;
          }
        }
      }
    }
    return result;
  }
}

static
PyObject  *
unpack (PyObject * self, PyObject * arg_list)
{
  char * format;
  int format_len;
  unsigned char * data;
  int data_len;
  int data_pos=0;

  PyObject * functions = NULL;

  if (!PyArg_ParseTuple (arg_list,
                         "s#s#|iO!",
                         &format,
                         &format_len,
                         &data,
                         &data_len,
                         &data_pos,
                         &PyDict_Type,
                         &functions
                         )) {
    return NULL;
  } else {
    PyObject * original_data_string = PyTuple_GetItem (arg_list, 1);
    PyObject * result = PyList_New (0);
    char ch;
    int num = 0;
    int i;
    char byte_order = format[0];
    int original_data_pos = data_pos;

    /* check for a specified byte order */
    switch (byte_order) {
    case 'L':
    case 'B':
      i = 1;
      break;
    case 'N':
      /* Native byte order */
      /* <endian> is computed when this module is initialized */
      byte_order = endian ? 'B' : 'L';
      i = 1;
      break;
    default:
      /* default to native if not specified */
      byte_order = endian ? 'B' : 'L';
      i = 0;
      break;
    }
    
#define ENOUGH_DATA(n)                                          \
    do {                                                        \
      if ((data_pos + n) > data_len) {                          \
        Py_DECREF (result);                                     \
        PyErr_SetString (PyExc_ValueError, "not enough data");  \
        return NULL;                                            \
      }                                                         \
    } while (0)

    while (ch = format[i]) {
      char * spec_start = format+i;
      i++;
      
      if ((ch >= '0') && (ch <= '9')) {
        num = (num * 10) + (ch - '0');
      } else {
        
        if (data_pos > data_len) {
          Py_DECREF (result);
          PyErr_SetString (PyExc_ValueError, "not enough data");
          return NULL;
        }
        
        /* handle multipliers by recursing */
        if (num > 0) {
          PyObject * spec;
          PyObject * full_spec;
          char * eos;
          int spec_len;
          /* build a new format string */
          /* <BYTE_ORDER> + <n>*<format> */
          switch (ch) {
          case 'b': case 'h': case 'l':
          case 'c': case 'd': case 'f':
          case 'x':
            spec = PyString_FromStringAndSize (&ch, 1);
            spec_len = 1;
            break;
          case '(':
            eos = strchr (spec_start, ')');
            if ((!eos) || (eos-format > format_len)) {
              PyErr_SetString (PyExc_ValueError, "unterminated bit field");
              Py_DECREF (result);
              return NULL;
            } else {
              spec_len = (eos-spec_start) + 1;
              spec = PyString_FromStringAndSize (spec_start, spec_len);
            }
            break;
          case '[':
            eos = strchr (spec_start, ']');
            if ((!eos) || (eos-format > format_len)) {
              PyErr_SetString (PyExc_ValueError, "unterminated bit field");
              Py_DECREF (result);
              return NULL;
            } else {
              spec_len = (eos-spec_start) + 1;
              spec = PyString_FromStringAndSize (spec_start, spec_len);
            }
            break;
          }
          /* make a one-character byte order spec */
          full_spec = PyString_FromStringAndSize (&byte_order, 1);
          /* now repeat the spec string */
          PyString_ConcatAndDel (&full_spec, PySequence_Repeat (spec, num));
          Py_DECREF (spec);
          /* recurse */
          {
            PyObject * unpacked;
            PyObject * args;
            PyObject * values;
            /* we can't just use the 's' character for Py_BuildValue because
             * our data string will (very likely) have embedded NULL characters */
            int munched;
            if (functions) {
              args = Py_BuildValue ("OOiO", full_spec, original_data_string, data_pos, functions);
            } else {
              args = Py_BuildValue ("OOi", full_spec, original_data_string, data_pos);
            }
            unpacked = unpack (NULL, args);
            Py_DECREF (args);
            if (!unpacked) {
              return NULL;
            } else if (!PyArg_ParseTuple (unpacked, "Oi", &values, &munched)) {
              return NULL;
            } else {
              PyList_Append (result, values);
              data_pos += munched;
              Py_DECREF (full_spec);
              i += spec_len - 1;
              num = 0;
            }
          }
        } else {
          switch (ch) {
            
            /* char */
          case 'c':
            ENOUGH_DATA (1);
            PyList_Append (result, PyString_FromStringAndSize ((const char *) data+data_pos, 1));
            data_pos++;
            break;

            /* byte */
            
          case 'b':
            ENOUGH_DATA (1);
            PyList_Append (result, PyInt_FromLong (((unsigned char *)data)[data_pos]));
            data_pos++;
            break;

            /* word/short */

          case 'h':
            {
              unsigned int x;
              ENOUGH_DATA (2);

              switch (byte_order) {
              case 'L':
                LITTLE_DECODE_WORD (x,data+data_pos);
                break;
              case 'B':
                BIG_DECODE_WORD (x,data+data_pos);
                break;
              }
              PyList_Append (result, PyInt_FromLong (x));
              data_pos += 2;
            }
          break;

          /* long */

          case 'l':
            {
              unsigned int x;
              ENOUGH_DATA (4);

              switch (byte_order) {
              case 'L':
                LITTLE_DECODE_LONG (x,data+data_pos);
                break;
              case 'B':
                BIG_DECODE_LONG (x,data+data_pos);
                break;
              }
              PyList_Append (result, PyInt_FromLong (x));
              data_pos += 4;
            }
          break;

          /* float */

          case 'f':
            {
              float x;
              ENOUGH_DATA (4);
              switch (byte_order) {
              case 'L':
                LITTLE_DECODE_FLOAT (x, data+data_pos);
                break;
              case 'B':
                BIG_DECODE_FLOAT (x, data+data_pos);
                break;
              }
              PyList_Append (result, PyFloat_FromDouble ((double) x));
              data_pos += 4;
            }
          break;

          /* double */

          case 'd':
            {
              double x;
              ENOUGH_DATA (8);
              switch (byte_order) {
              case 'L':
                LITTLE_DECODE_DOUBLE (x, data+data_pos);
                break;
              case 'B':
                BIG_DECODE_DOUBLE (x, data+data_pos);
                break;
              }
              PyList_Append (result, PyFloat_FromDouble (x));
              data_pos += 8;
            }
          break;
            
          /* bitfield */

          case '(':
            {
              PyObject * bit_length_list = PyList_New (0);
              int new_format_pos = get_bit_length_list (bit_length_list, format, i);
              if (new_format_pos == -1) {
                /* get_bit_length_list will set the error */
                Py_DECREF (bit_length_list);
                Py_DECREF (result);
                return NULL;
              } else {
                int new_data_pos = unpack_bitfield (bit_length_list, result, data, data_pos, data_len);
                if (new_data_pos == -1) {
                  return NULL;
                } else {
                  /* unpack_bitfield appends to the result list itself */
                  Py_DECREF (bit_length_list);
                  data_pos = new_data_pos;
                  i = new_format_pos;
                }
              }
            }
          break;

          /* pad byte */
            
          case 'x':
            data_pos++;
            break;


            /* user function */

          case '[':
            {
              char * eos = strchr (format+i, ']');
              if (!eos) {
                Py_DECREF (result);
                PyErr_SetString (PyExc_ValueError, "unterminated user function name");
                return NULL;
              } else {
                PyObject * key = PyString_FromStringAndSize (format+i, eos-(format+i));
                PyObject * fun;
                if ((!functions) || (!(fun = PyDict_GetItem (functions, key)))) {
                  PyErr_SetString (PyExc_ValueError, "unknown user function");
                  Py_DECREF (key);
                  Py_DECREF (result);
                  return NULL;
                } else {
                  Py_DECREF (key);
                  if (!PyCallable_Check (fun)) {
                    PyErr_SetString (PyExc_ValueError, "not a callable function");
                    Py_DECREF (result);
                    return NULL;
                  } else {
                    int munched;
                    PyObject * decoded_data;
                    PyObject * user_function_result;
                    Py_INCREF (original_data_string);
                    user_function_result = PyEval_CallObject (
                      fun,
                      Py_BuildValue ("OOi", result, original_data_string, data_pos)
                      );
                    Py_DECREF (original_data_string);
                    if (!user_function_result) {
                      Py_DECREF (result);
                      return NULL;
                    } else if (!PyArg_ParseTuple (user_function_result,
                                                  "O!i",
                                                  &PyTuple_Type,
                                                  &decoded_data,
                                                  &munched)) {
                      PyErr_SetString (PyExc_ValueError, "bad result from user function");
                      Py_DECREF (user_function_result);
                      Py_DECREF (result);
                      return NULL;
                    } else {
                      /* append the user-parsed data to the current result list */
                      int num_items = PyTuple_Size (decoded_data);
                      int j;
                      for (j = 0; j < num_items; j++) {
                        PyObject * elem = PyTuple_GetItem (decoded_data, j);
                        Py_INCREF (elem);
                        PyList_Append (result, elem);
                      }
                      data_pos += munched;
                      Py_DECREF (user_function_result);
                      i = (eos-format)+1;
                    }
                  }
                }
              }
            }
          break; /* end case '[' */

          default:
            //PyErr_SetObject (PyExc_ValueError, Py_BuildValue ("si", "unknown format character", ch));
            PyErr_SetString (PyExc_ValueError, "unknown format character");
            Py_DECREF (result);
            return NULL;
            break;
          }
        }
      }
    }
    {
      PyObject * tuple_result;
      PyObject * final_result;
      /* convert to a tuple */
      tuple_result = PyList_AsTuple (result);
      /* combine with data position into a new tuple */
      final_result = Py_BuildValue ("Oi", tuple_result, (int)(data_pos - original_data_pos));
      Py_DECREF (tuple_result);
      return (final_result);
    }
  }
}
    
static struct PyMethodDef npstruct_module_methods[] = {
  {"pack",                  pack,                       1},
  {"unpack",                unpack,                     1},
  {NULL, NULL}              /* sentinel */
};


/* From ILU */
static int
big_endian (void) {
  /* Are we little or big endian?  From Harbison&Steele.  */
  union
  {
    long l;
    char c[sizeof (long)];
  } u;
  u.l = 1;
  endian = (u.c[sizeof (long) - 1] == 1);
  return endian;
}

void
initnpstruct (void)
{
  PyObject *m, *d;
  m = Py_InitModule ("npstruct", npstruct_module_methods);
  d = PyModule_GetDict(m);

  PyDict_SetItemString (
    d,
    "endian",
    PyString_FromString (big_endian() ? "big" : "little")
    );
    
  if (PyErr_Occurred()) {
    Py_FatalError ("Can't initialize module npstruct");
  }
}

