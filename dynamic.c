// SPDX-License-Identifier: LGPL-2.1-or-later
/*
 * libiio - Library for interfacing industrial I/O (IIO) devices
 *
 * Copyright (C) 2021 Analog Devices, Inc.
 * Author: Paul Cercueil <paul.cercueil@analog.com>
 */

#include "dynamic.h"
#include "iio-backend.h"
#include "iio-config.h"
#include "iio-debug.h"
#include "iio-private.h"

#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <sys/types.h>

struct iio_module {
	const struct iio_context_params *params;
	void *lib;
	char *name;
};

struct iio_module * iio_open_module(const struct iio_context_params *params,
				    const char *name)
{
	char buf[PATH_MAX];
	struct iio_module *module;
	int err = -ENOMEM;

	module = zalloc(sizeof(*module));
	if (!module)
		return ERR_PTR(-ENOMEM);

	module->name = strdup(name);
	if (!module->name)
		goto err_free_module;

	module->params = params;

	iio_snprintf(buf, sizeof(buf),
		     IIO_MODULES_DIR "libiio-%s" IIO_LIBRARY_SUFFIX, name);

	prm_dbg(params, "Looking for plugin: \'%s\'\n", buf);

	module->lib = iio_dlopen(buf);
	if (!module->lib) {
		prm_err(params, "Unable to open plug-in\n");
		err = -ENOSYS;
		goto err_free_name;
	}

	return module;

err_free_name:
	free(module->name);
err_free_module:
	free(module);
	return ERR_PTR(err);
}

void iio_release_module(struct iio_module *module)
{
	iio_dlclose(module->lib);
	free(module->name);
	free(module);
}

const struct iio_backend * iio_module_get_backend(struct iio_module *module)
{
	const struct iio_backend *backend;
	char buf[1024];

	iio_snprintf(buf, sizeof(buf), "iio_%s_backend", module->name);

	backend = iio_dlsym(module->lib, buf);
	if (!backend) {
		prm_err(module->params, "No \'%s\' symbol\n", buf);
		return ERR_PTR(-EINVAL);
	}

	return backend;
}

static const struct iio_backend *
get_iio_backend(const struct iio_context_params *params,
		const char *name, struct iio_module **libp)
{
	const struct iio_backend *backend;
	struct iio_module *lib;

	lib = iio_open_module(params, name);
	if (IS_ERR(lib)) {
		prm_dbg(params, "Unable to open plug-in\n");
		return (void *) lib;
	}

	backend = iio_module_get_backend(lib);
	if (IS_ERR(backend)) {
		prm_err(params, "Module is not a backend\n");
		iio_release_module(lib);
		return (void *) backend;
	}

	*libp = lib;

	return backend;
}

struct iio_context *
iio_create_dynamic_context(const struct iio_context_params *params,
			   const char *uri)
{
	struct iio_context_params params2 = *params;
	const struct iio_backend *backend;
	struct iio_context *ctx;
	const char *ptr;
	char buf[256];
	struct iio_module *lib;

	ptr = strchr(uri, ':');

	if (!ptr) {
		prm_err(params, "Invalid URI: %s\n", uri);
		errno = EINVAL;
		return NULL;
	}

	iio_snprintf(buf, sizeof(buf), "%.*s", (int) (ptr - uri), uri);

	backend = get_iio_backend(params, buf, &lib);
	if (IS_ERR(backend)) {
		errno = -PTR_ERR(backend);
		return NULL;
	}

	if (!backend->ops || !backend->ops->create) {
		prm_err(params, "Backend has no create function\n");
		errno = EINVAL;
		goto out_release_module;
	}

	prm_dbg(params, "Found backend: %s\n", backend->name);

	if (!params2.timeout_ms)
		params2.timeout_ms = backend->default_timeout_ms;

	uri += strlen(backend->uri_prefix);
	ctx = (*backend->ops->create)(&params2, uri);
	if (!ctx)
		goto out_release_module;

	ctx->lib = lib;
	return ctx;

out_release_module:
	iio_release_module(lib);
	return NULL;
}
