// SPDX-License-Identifier: LGPL-2.1-or-later OR MIT
/*
 * libiio - Library for interfacing industrial I/O (IIO) devices
 *
 * Copyright (C) 2015 Analog Devices, Inc.
 * Author: Paul Cercueil <paul.cercueil@analog.com>
 */

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading.Tasks;

namespace iio
{
    /// <summary><see cref="iio.Attr"/> class:
    /// Contains the representation of an iio_attr.</summary>
    public class Attr
    {
        [DllImport(IioLib.dllname, CallingConvention = CallingConvention.Cdecl)]
        private static extern int iio_attr_read_raw(IntPtr attr,
                [Out()] StringBuilder dst, uint len);

        [DllImport(IioLib.dllname, CallingConvention = CallingConvention.Cdecl)]
        private static extern int iio_attr_write_raw(IntPtr attr, IntPtr src,
                uint len);

        [DllImport(IioLib.dllname, CallingConvention = CallingConvention.Cdecl)]
        private static extern IntPtr iio_attr_get_name(IntPtr attr);

        [DllImport(IioLib.dllname, CallingConvention = CallingConvention.Cdecl)]
        private static extern IntPtr iio_attr_get_filename(IntPtr attr);

        [DllImport(IioLib.dllname, CallingConvention = CallingConvention.Cdecl)]
        private static extern IntPtr iio_attr_get_static_value(IntPtr attr);

        internal IntPtr attr;

        /// <summary>The name of this attribute.</summary>
        public readonly string name;

        /// <summary>The filename in sysfs to which this attribute is bound.</summary>
        public readonly string filename;

        internal Attr(IntPtr attr)
        {
            this.attr = attr;
            this.name = Marshal.PtrToStringAnsi(iio_attr_get_name(attr));
            this.filename = Marshal.PtrToStringAnsi(iio_attr_get_filename(attr));
        }

        /// <summary>Read the value of this attribute as a <c>string</c>.</summary>
        /// <exception cref="IioLib.IIOException">The attribute could not be read.</exception>
        public string read()
        {
            StringBuilder builder = new StringBuilder(1024);
            int err = iio_attr_read_raw(attr, builder, (uint)builder.Capacity);
            if (err < 0)
            {
                throw new IIOException("Unable to read attribute", err);
            }
            return builder.ToString();
        }

        /// <summary>Set this attribute to the value contained in the <c>string</c> argument.</summary>
        /// <param name="val">The <c>string</c> value to set the parameter to.</param>
        /// <exception cref="IioLib.IIOException">The attribute could not be written.</exception>
        public void write(string val)
        {
            IntPtr valptr = Marshal.StringToHGlobalAnsi(val);
            int err = iio_attr_write_raw(attr, valptr, (uint)val.Length);
            if (err < 0)
                throw new IIOException("Unable to write attribute", err);
        }

        /// <summary>Read the value of this attribute as a <c>bool</c>.</summary>
        /// <exception cref="IioLib.IIOException">The attribute could not be read.</exception>
        public bool read_bool()
        {
            string val = read();
            return (val.CompareTo("1") == 0) || (val.CompareTo("Y") == 0);
        }

        /// <summary>Read the value of this attribute as a <c>double</c>.</summary>
        /// <exception cref="IioLib.IIOException">The attribute could not be read.</exception>
        public double read_double()
        {
            return double.Parse(read(), CultureInfo.InvariantCulture);
        }

        /// <summary>Read the value of this attribute as a <c>long</c>.</summary>
        /// <exception cref="IioLib.IIOException">The attribute could not be read.</exception>
        public long read_long()
        {
            return long.Parse(read(), CultureInfo.InvariantCulture);
        }

        /// <summary>Set this attribute to the value contained in the <c>bool</c> argument.</summary>
        /// <param name="val">The <c>bool</c> value to set the parameter to.</param>
        /// <exception cref="IioLib.IIOException">The attribute could not be written.</exception>
        public void write(bool val)
        {
            if (val)
            {
                write("1");
            }
            else
            {
                write("0");
            }
        }

        /// <summary>Set this attribute to the value contained in the <c>long</c> argument.</summary>
        /// <param name="val">The <c>long</c> value to set the parameter to.</param>
        /// <exception cref="IioLib.IIOException">The attribute could not be written.</exception>
        public void write(long val)
        {
            write(val.ToString(CultureInfo.InvariantCulture));
        }

        /// <summary>Set this attribute to the value contained in the <c>double</c> argument.</summary>
        /// <param name="val">The <c>double</c> value to set the parameter to.</param>
        /// <exception cref="IioLib.IIOException">The attribute could not be written.</exception>
        public void write(double val)
        {
            write(val.ToString(CultureInfo.InvariantCulture));
        }
    }
}
