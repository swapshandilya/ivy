# global
from hypothesis import strategies as st

# local
import ivy_tests.test_ivy.helpers as helpers
from ivy_tests.test_ivy.helpers import handle_test
import ivy


@handle_test(
    fn_tree="functional.ivy.experimental.l1_normalize",
    dtype_values_axis=helpers.dtype_values_axis(
        available_dtypes=helpers.get_dtypes("valid"), valid_axis=True
    ),
)
def test_l1_normalize(*, dtype_values_axis, test_flags, backend_fw, fn_name, on_device):
    x_dtype, x, axis = dtype_values_axis
    helpers.test_function(
        fw=backend_fw,
        test_flags=test_flags,
        fn_name=fn_name,
        on_device=on_device,
        rtol_=1e-1,
        atol_=1e-1,
        input_dtypes=x_dtype,
        x=x,
        axis=axis,
    )


@st.composite
def _instance_and_batch_norm_helper(draw, *, min_dims=1, test_function="instance_norm"):
    mixed_fn_compos = draw(st.booleans())
    is_torch_backend = ivy.current_backend_str() == "torch"
    data_format = draw(st.sampled_from(["NSC", "NCS"]))
    shape1, shape2, shape3, shape4 = draw(
        helpers.mutually_broadcastable_shapes(
            num_shapes=4, min_dims=min_dims, min_side=2
        )
    )
    shape = helpers.broadcast_shapes(shape1, shape2, shape3, shape4)

    if (test_function == "instance_norm") or (is_torch_backend and not mixed_fn_compos):
        shape1 = shape2 = shape3 = shape4 = (shape[-1],)

    if data_format == "NCS":
        shape = (shape[0], shape[-1], *shape[1:-1])

    x_dtype, x = draw(
        helpers.dtype_and_values(
            available_dtypes=helpers.get_dtypes(
                "float",
                mixed_fn_compos=mixed_fn_compos,
            ),
            large_abs_safety_factor=24,
            small_abs_safety_factor=24,
            safety_factor_scale="log",
            shape=shape,
            max_value=999,
            min_value=-1001,
        )
    )

    _, mean = draw(
        helpers.dtype_and_values(
            dtype=x_dtype,
            shape=shape1,
            min_value=-1001,
            max_value=999,
            large_abs_safety_factor=24,
            small_abs_safety_factor=24,
            safety_factor_scale="log",
        )
    )
    _, variance = draw(
        helpers.dtype_and_values(
            dtype=x_dtype,
            shape=shape2,
            min_value=0,
            max_value=999,
            large_abs_safety_factor=24,
            small_abs_safety_factor=24,
            safety_factor_scale="log",
        )
    )
    _, offset = draw(
        helpers.dtype_and_values(
            dtype=x_dtype,
            shape=shape3,
            min_value=-1001,
            max_value=999,
            large_abs_safety_factor=24,
            small_abs_safety_factor=24,
            safety_factor_scale="log",
        )
    )
    _, scale = draw(
        helpers.dtype_and_values(
            dtype=x_dtype,
            shape=shape4,
            min_value=-1001,
            max_value=999,
            large_abs_safety_factor=24,
            small_abs_safety_factor=24,
            safety_factor_scale="log",
        )
    )
    eps = draw(
        helpers.floats(min_value=1e-5, max_value=0.1, mixed_fn_compos=mixed_fn_compos)
    )
    momentum = draw(
        helpers.floats(min_value=0.0, max_value=1.0, mixed_fn_compos=mixed_fn_compos)
    )
    return (
        x_dtype,
        x[0],
        mean[0],
        variance[0],
        offset[0],
        scale[0],
        eps,
        momentum,
        data_format,
    )


@handle_test(
    fn_tree="functional.ivy.experimental.instance_norm",
    data=_instance_and_batch_norm_helper(min_dims=3),
    training=st.booleans(),
)
def test_instance_norm(*, data, training, test_flags, backend_fw, fn_name, on_device):
    x_dtype, x, mean, variance, offset, scale, eps, momentum, data_format = data
    helpers.test_function(
        fw=backend_fw,
        test_flags=test_flags,
        fn_name=fn_name,
        on_device=on_device,
        xs_grad_idxs=[[0, 0]],
        rtol_=1e-1,
        atol_=1e-1,
        input_dtypes=x_dtype,
        x=x,
        mean=mean,
        variance=variance,
        scale=scale,
        offset=offset,
        eps=eps,
        training=training,
        momentum=momentum,
        data_format=data_format,
    )


# batch_norm
@handle_test(
    fn_tree="functional.ivy.experimental.batch_norm",
    data=_instance_and_batch_norm_helper(min_dims=2, test_function="batch_norm"),
    training=st.booleans(),
)
def test_batch_norm(*, data, training, test_flags, backend_fw, fn_name, on_device):
    x_dtype, x, mean, variance, offset, scale, eps, momentum, data_format = data
    helpers.test_function(
        fw=backend_fw,
        test_flags=test_flags,
        fn_name=fn_name,
        on_device=on_device,
        xs_grad_idxs=[[0, 0]],
        rtol_=1e-2,
        atol_=1e-2,
        input_dtypes=x_dtype,
        x=x,
        mean=mean,
        variance=variance,
        scale=scale,
        offset=offset,
        eps=eps,
        training=training,
        momentum=momentum,
        data_format=data_format,
    )


@st.composite
def _group_norm_helper(draw):
    data_format = draw(st.sampled_from(["NSC", "NCS"]))
    shape = draw(
        helpers.get_shape(
            min_num_dims=2, max_num_dims=4, min_dim_size=2, max_dim_size=4
        )
    )
    channel_size = shape[-1]
    group_list = [*range(1, 4)]
    group_list = list(filter(lambda x: (channel_size % x == 0), group_list))
    num_groups = draw(st.sampled_from(group_list))
    if data_format == "NCS":
        shape = (shape[0], shape[-1], *shape[1:-1])
    x_dtype, x = draw(
        helpers.dtype_and_values(
            available_dtypes=helpers.get_dtypes(
                "float",
            ),
            shape=shape,
            large_abs_safety_factor=50,
            small_abs_safety_factor=50,
            safety_factor_scale="log",
        )
    )
    _, offset = draw(
        helpers.dtype_and_values(
            dtype=x_dtype,
            shape=(channel_size,),
            large_abs_safety_factor=50,
            small_abs_safety_factor=50,
            safety_factor_scale="log",
        )
    )

    _, scale = draw(
        helpers.dtype_and_values(
            dtype=x_dtype,
            shape=(channel_size,),
            large_abs_safety_factor=50,
            small_abs_safety_factor=50,
            safety_factor_scale="log",
        )
    )
    eps = draw(helpers.floats(min_value=1e-5, max_value=0.1))
    return x_dtype, x[0], num_groups, data_format, scale[0], offset[0], eps


# group_norm
@handle_test(
    fn_tree="functional.ivy.experimental.group_norm",
    data=_group_norm_helper(),
)
def test_group_norm(
    *,
    data,
    test_flags,
    backend_fw,
    fn_name,
    on_device,
):
    x_dtype, x, num_groups, data_format, scale, offset, eps = data
    helpers.test_function(
        fw=backend_fw,
        test_flags=test_flags,
        fn_name=fn_name,
        on_device=on_device,
        xs_grad_idxs=[[0, 0]],
        rtol_=1e-1,
        atol_=1e-1,
        input_dtypes=x_dtype,
        x=x,
        num_groups=num_groups,
        scale=scale,
        offset=offset,
        eps=eps,
        data_format=data_format,
    )
