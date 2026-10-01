"""
collisions: puck-vs-paddle collision handling.
"""

import math


COLLISION_EPSILON = 1e-6


def _reflect_velocity(puck, normal_x, normal_y):
    """Reflect the puck's velocity across the supplied collision normal."""
    velocity_dot_normal = puck.vx * normal_x + puck.vy * normal_y

    # Only reflect while moving into the paddle. This prevents the positional
    # correction from causing repeated bounces while the puck is leaving it.
    if velocity_dot_normal < 0:
        puck.vx -= 2 * velocity_dot_normal * normal_x
        puck.vy -= 2 * velocity_dot_normal * normal_y
        return True

    return False


def handle_paddle_collision(puck, paddle):
    """
    Detect and resolve a puck/paddle collision.

    Both objects are treated as circles. The puck's swept path from its
    previous position to its current position is checked, so a fast puck
    cannot pass through a paddle between frames.

    When a collision is found, the puck is placed just outside the paddle and
    its velocity is reflected across the collision normal. This handles
    angled impacts correctly and prevents the puck from becoming embedded in
    the paddle.

    Returns True if a collision was handled this frame.
    """
    combined_radius = puck.radius + paddle.radius
    combined_radius_sq = combined_radius * combined_radius

    start_x = getattr(puck, "previous_x", puck.x)
    start_y = getattr(puck, "previous_y", puck.y)
    end_x = puck.x
    end_y = puck.y

    # Handle an overlap at the current position first. This also covers a
    # puck that was already embedded in the paddle before this function ran.
    dx = end_x - paddle.x
    dy = end_y - paddle.y
    distance_sq = dx * dx + dy * dy

    if distance_sq <= combined_radius_sq:
        distance = math.sqrt(distance_sq)

        if distance > COLLISION_EPSILON:
            normal_x = dx / distance
            normal_y = dy / distance
        else:
            # If the centers coincide, use the opposite of the puck's motion
            # as the normal so the puck is pushed back along its incoming path.
            speed = math.hypot(puck.vx, puck.vy)
            if speed > COLLISION_EPSILON:
                normal_x = -puck.vx / speed
                normal_y = -puck.vy / speed
            else:
                normal_x, normal_y = 1.0, 0.0

        puck.x = paddle.x + normal_x * (combined_radius + COLLISION_EPSILON)
        puck.y = paddle.y + normal_y * (combined_radius + COLLISION_EPSILON)
        _reflect_velocity(puck, normal_x, normal_y)
        return True

    # Swept circle-vs-circle test. Solve for the first point where the puck's
    # center reaches the sum of the two radii from the paddle center.
    segment_x = end_x - start_x
    segment_y = end_y - start_y
    relative_start_x = start_x - paddle.x
    relative_start_y = start_y - paddle.y

    segment_length_sq = segment_x * segment_x + segment_y * segment_y
    if segment_length_sq <= COLLISION_EPSILON:
        return False

    a = segment_length_sq
    b = 2.0 * (relative_start_x * segment_x + relative_start_y * segment_y)
    c = (
        relative_start_x * relative_start_x
        + relative_start_y * relative_start_y
        - combined_radius_sq
    )

    discriminant = b * b - 4.0 * a * c
    if discriminant < 0:
        return False

    sqrt_discriminant = math.sqrt(max(0.0, discriminant))
    first_t = (-b - sqrt_discriminant) / (2.0 * a)
    second_t = (-b + sqrt_discriminant) / (2.0 * a)

    collision_t = None
    for t in (first_t, second_t):
        if 0.0 <= t <= 1.0:
            collision_t = t
            break

    if collision_t is None:
        return False

    contact_x = start_x + segment_x * collision_t
    contact_y = start_y + segment_y * collision_t

    normal_x = contact_x - paddle.x
    normal_y = contact_y - paddle.y
    normal_length = math.hypot(normal_x, normal_y)

    if normal_length <= COLLISION_EPSILON:
        speed = math.hypot(puck.vx, puck.vy)
        if speed <= COLLISION_EPSILON:
            return False
        normal_x = -puck.vx / speed
        normal_y = -puck.vy / speed
    else:
        normal_x /= normal_length
        normal_y /= normal_length

    # Remove all overlap at the collision point before reflecting. The small
    # epsilon keeps floating-point error from leaving the puck intersecting
    # the paddle on the next frame.
    puck.x = paddle.x + normal_x * (combined_radius + COLLISION_EPSILON)
    puck.y = paddle.y + normal_y * (combined_radius + COLLISION_EPSILON)

    _reflect_velocity(puck, normal_x, normal_y)
    return True
