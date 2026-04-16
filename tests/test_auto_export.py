from auto_export import (
  BASELINE_BOUNDS,
  BTN_3DOTS_X,
  BTN_3DOTS_Y,
  BTN_COPY_LINK_X,
  BTN_COPY_LINK_Y_CANDIDATES,
  FIRST_ITEM_X,
  FIRST_ITEM_Y,
  ITEM_HEIGHT,
  LIST_AREA_X,
  LIST_AREA_Y,
  get_card_point,
  get_copy_link_points,
  get_list_area_point,
  get_three_dots_point,
)


def test_relative_mapping_reproduces_known_good_baseline_points():
  assert get_list_area_point(BASELINE_BOUNDS) == (LIST_AREA_X, LIST_AREA_Y)
  assert get_card_point(BASELINE_BOUNDS, 0) == (FIRST_ITEM_X, FIRST_ITEM_Y)
  assert get_card_point(BASELINE_BOUNDS, 1) == (FIRST_ITEM_X, FIRST_ITEM_Y + ITEM_HEIGHT)
  assert get_three_dots_point(BASELINE_BOUNDS) == (BTN_3DOTS_X, BTN_3DOTS_Y)
  assert get_copy_link_points(BASELINE_BOUNDS) == [
    (BTN_COPY_LINK_X, BTN_COPY_LINK_Y_CANDIDATES[0]),
    (BTN_COPY_LINK_X, BTN_COPY_LINK_Y_CANDIDATES[1]),
  ]


def test_relative_mapping_translates_with_window_position_change():
  moved_bounds = (100, 50, BASELINE_BOUNDS[2], BASELINE_BOUNDS[3])

  list_x, list_y = get_list_area_point(moved_bounds)
  card_x, card_y = get_card_point(moved_bounds, 0)
  dots_x, dots_y = get_three_dots_point(moved_bounds)
  copy_points = get_copy_link_points(moved_bounds)

  assert (list_x, list_y) == (LIST_AREA_X + 108, LIST_AREA_Y + 58)
  assert (card_x, card_y) == (FIRST_ITEM_X + 108, FIRST_ITEM_Y + 58)
  assert (dots_x, dots_y) == (BTN_3DOTS_X + 108, BTN_3DOTS_Y + 58)
  assert copy_points == [
    (BTN_COPY_LINK_X + 108, BTN_COPY_LINK_Y_CANDIDATES[0] + 58),
    (BTN_COPY_LINK_X + 108, BTN_COPY_LINK_Y_CANDIDATES[1] + 58),
  ]


def test_card_spacing_scales_from_window_height():
  taller_bounds = (-8, -8, BASELINE_BOUNDS[2], 1200)
  x0, y0 = get_card_point(taller_bounds, 0)
  x1, y1 = get_card_point(taller_bounds, 1)

  assert x0 == x1
  assert y1 > y0
  assert y1 - y0 == round(1200 * (ITEM_HEIGHT / BASELINE_BOUNDS[3]))
