# MATATAG Grade 2-3 Competency to Generator Mapping

This document maps every MATATAG Grade 2 and Grade 3 learning competency to its corresponding generator template, template function, difficulty dimensions, and visual option availability.

---

## Grade 2

### Measurement and Geometry

#### Quarter 1

1. **Competency**: Represent and describe circles, half circles and quarter circles.
   - **Content Area**: Measurement and Geometry
   - **Generator**: geometry_props
   - **Template Function**: `_gen_geometry_props()`
   - **Template Problem Example**: "How many sides does a circle have?" (Note: Circle has 0 sides - this asks about curved vs straight distinction)
   - **Difficulty Dimensions**:
     - shape_complexity: 0.0 - Basic shapes (circle, half circle, quarter circle)
     - property_type: 0.0 - Count sides/corners or identify curved vs straight
     - angle_precision: 0.0 - Right angles only (for quarter circles)
     - polygon_sides_max: N/A - Not applicable to circles
   - **Visual Option**: Yes - Could use Categorize visual to sort shapes
   - **Status**: Partial - Basic identification supported

   **Visual Skeleton Details**:
   - **Visual Type**: Categorize
   - **Template Function**: `_gen_categorize()`
   - **Visual Params**:
     - `categories`: ["Circles", "Half Circles", "Quarter Circles", "Other Shapes"]
     - `items`: List of shape names or images to sort
     - `correct_categories`: Mapping of each item to its category
   - **Example Output**:
     ```json
     {
       "categories": ["Curved Shapes", "Shapes with Straight Edges"],
       "items": ["Circle", "Half Circle", "Quarter Circle", "Square", "Triangle"],
       "correct_categories": {
         "Circle": "Curved Shapes",
         "Half Circle": "Curved Shapes",
         "Quarter Circle": "Curved Shapes",
         "Square": "Shapes with Straight Edges",
         "Triangle": "Shapes with Straight Edges"
       }
     }
     ```
    - **Question Modes**: interactive (drag items to categories), mcq (select correct category for item), fill_in (type category name)

   **MCQ Skeleton Details**:
   - **Sub-Generator**: `_gen_geo_circles`
   - **Scope**: All circle/half-circle/quarter-circle questions (curved vs straight edges)
   - **Stem Variations** (6 question templates, 3 stems each):
     1. "How many straight edges does a circle have?" → 0
     2. "A circle has ___ straight sides." → 0
     3. "Count the straight edges of a circle." → 0
     4. "How many straight edges does a half circle have?" → 1
     5. "A half circle (semicircle) has ___ straight edge(s)." → 1
     6. "Count the straight edges of a semicircle." → 1
     7. "How many straight edges does a quarter circle have?" → 2
     8. "A quarter circle has ___ straight edge(s)." → 2
     9. "Count the straight sides of a quarter circle." → 2
     10. "Which shape has NO straight edges?" → circle
     11. "Which of these shapes has only curved edges?" → circle
     12. "Identify the shape with zero straight sides." → circle
     13. "A quarter circle looks like a slice of:" → pizza slice
     14. "Which everyday object looks like a quarter circle?" → pizza slice
     15. "A quarter circle resembles a:" → pizza slice
     16. "How many curved edges does a half circle have?" → 1
     17. "A semicircle has ___ curved edge(s)." → 1
     18. "Count the curved edges of a half circle." → 1
   - **Traps**:
     | Code | Description |
     |------|-------------|
     | `gp_curve_as_side` | Counted the curved edge as a straight side |
     | `gp_forgot_diameter` | Didn't count the flat (diameter) edge of semicircle |
     | `gp_forgot_one` | Missed one of the two radii in quarter circle |
     | `gp_has_diameter` | Confused half circle (has 1 straight edge) with circle (0) |
     | `gp_has_radii` | Confused quarter circle (has 2 straight edges) with circle (0) |
     | `gp_not_circle` | Selected oval instead of circle |
   - **Answer Format**: Integer string or shape name
   - **Status**: Covered

2. **Competency**: Compose and decompose composite figures made up of squares, rectangles, triangles, circles, half circles, and quarter circles, using cut-outs and square grids.
   - **Content Area**: Measurement and Geometry
   - **Generator**: geometry_props
   - **Template Function**: `_gen_geometry_props()` (compose/decompose branch)
   - **Template Problem Example**: "Two triangles can be put together to make a: [square/circle/triangle/pentagon]"
   - **Difficulty Dimensions**:
     - shape_complexity: 0.3-0.5 - Composite figures
     - property_type: 0.5 - Composition and decomposition
     - polygon_sides_max: 4 - Squares and rectangles
   - **Visual Option**: Yes - GridArea visual could show composite figures
   - **Status**: Covered

   **Visual Skeleton Details**:
   - **Visual Type**: GridArea
   - **Template Function**: `_gen_grid_area()`
   - **Visual Params**:
     - `grid_size`: [10, 10] - Grid dimensions
     - `shape_type`: "composite" - L-shape, rectangle, or composite
     - `components`: List of component shapes with positions
     - `correct_count`: Total area in square units
     - `width`: Overall width (for rectangles)
     - `height`: Overall height (for rectangles)
   - **Example Output**:
     ```json
     {
       "grid_size": [10, 10],
       "shape_type": "L_shape",
       "components": [
         {"type": "rectangle", "width": 4, "height": 3, "x": 0, "y": 0},
         {"type": "rectangle", "width": 2, "height": 3, "x": 4, "y": 0}
       ],
       "correct_count": 18,
       "width": null,
       "height": null
     }
     ```
    - **Question Modes**: interactive (shade squares on grid), mcq (select correct area), fill_in (type the total area)

   **MCQ Skeleton Details**:
   - **Sub-Generator**: `_gen_geo_compose_shapes`
   - **Scope**: All compose/decompose shape questions — combining and splitting 2D figures
   - **Stem Variations** (8 question templates, 3 stems each):
     1. "Two triangles can be put together to make a:" → rectangle
     2. "If you join two identical right triangles, you can form a:" → rectangle
     3. "Combining two equal triangles along their longest side makes a:" → rectangle
     4. "A rectangle can be cut into two equal:" → triangles
     5. "If you cut a rectangle diagonally, you get two:" → triangles
     6. "Dividing a rectangle with a diagonal line gives:" → triangles
     7. "Four small squares can be arranged to make a:" → larger square
     8. "Putting 4 equal squares together (2 by 2) forms a:" → larger square
     9. "If you combine 4 unit squares in a 2x2 grid, you get a:" → larger square
     10. "How many triangles can a square be divided into by cutting both diagonals?" → 4
     11. "If you draw both diagonals of a square, how many triangles are formed?" → 4
     12. "Cutting a square along both diagonals creates ___ triangles." → 4
     13. "A square and a triangle placed side by side can look like a:" → house (pentagon)
     14. "Combining a square with a triangle on top makes the shape of a:" → house (pentagon)
     15. "A triangle on top of a square resembles a:" → house (pentagon)
     16. "Two rectangles placed end-to-end make a:" → longer rectangle
     17. "Joining two identical rectangles along their shorter side creates a:" → longer rectangle
     18. "Combine two equal rectangles side by side to form a:" → longer rectangle
     19. "An L-shape can be decomposed into:" → 2 rectangles
     20. "An L-shaped figure is made up of:" → 2 rectangles
     21. "You can break an L-shape into:" → 2 rectangles
     22. "How many squares make up a 2x3 rectangle?" → 6
     23. "A rectangle that is 2 squares wide and 3 squares long contains ___ squares." → 6
     24. "Count the unit squares inside a 2 by 3 rectangle." → 6
   - **Traps**:
     | Code | Description |
     |------|-------------|
     | `gp_wrong_shape` | Selected incorrect resulting shape |
     | `gp_same_shape` | Said combining two triangles makes another triangle |
     | `gp_one_diagonal` | Only counted triangles from one diagonal (2 instead of 4) |
     | `gp_too_many_sides` | Overcounted sides of composite figure |
     | `gp_too_few` | Undercounted components (1 rectangle instead of 2) |
     | `gp_too_many` | Overcounted components (3 instead of 2) |
     | `gp_close_shape` | Selected a similar but incorrect shape (rectangle vs square) |
     | `gp_wrong_arrangement` | Assumed wrong spatial arrangement |
   - **Answer Format**: Shape name or integer count
   - **Status**: Covered

3. **Competency**: Describe and draw the effect of one-direction multi-step slide (or translation) in basic shapes and figures.
   - **Content Area**: Measurement and Geometry
   - **Generator**: geometry_props (conceptual branch)
   - **Template Function**: `_gen_geometry_props()`
   - **Template Problem Example**: "Which shape has more sides: a triangle or a square?"
   - **Difficulty Dimensions**:
     - shape_complexity: 0.3 - Basic shapes
     - property_type: 0.5 - Transformation concepts
     - abstraction_level: 0.5 - Spatial reasoning required
   - **Visual Option**: Yes - GridArea visual could show translation
   - **Status**: Partial - Generator falls back to shape properties

   **Visual Skeleton Details**:
   - **Visual Type**: GridArea
   - **Template Function**: `_gen_grid_area()`
   - **Visual Params**:
     - `grid_size`: [10, 10] - Grid dimensions
     - `shape_type`: "translatable_shape" - Shape that can be slid
     - `initial_position`: [x, y] - Starting coordinates
     - `translation`: [dx, dy] - Translation vector (steps right/down)
     - `correct_count`: Final position coordinates
   - **Example Output**:
     ```json
     {
       "grid_size": [10, 10],
       "shape_type": "translatable_shape",
       "initial_position": [2, 3],
       "translation": [3, 2],
       "correct_count": [5, 5]
     }
     ```
    - **Question Modes**: interactive (drag shape to final position), mcq (select correct end position), fill_in (type coordinates)

   **MCQ Skeleton Details**:
   - **Sub-Generator**: `_gen_geo_translations` (single-direction mode)
   - **Scope**: One-direction slides on a coordinate grid
   - **Stem Variations**:
     1. "A shape is at ({x}, {y}). It slides {d} units {direction}. Where is it now?"
     2. "Start at position ({x}, {y}). Move {d} squares {direction}. New position?"
     3. "After sliding {d} units {direction} from ({x}, {y}), the shape is at:"
   - **Variables**: start_x (1-6), start_y (1-6), distance (1-5), direction (right/left/up/down)
   - **Traps**:
     | Code | Description |
     |------|-------------|
     | `gp_wrong_direction` | Moved opposite direction (e.g., left instead of right) |
     | `gp_moved_both_axes` | Added distance to both x and y instead of one |
     | `gp_no_move` | Gave original position unchanged |
   - **Answer Format**: "(x, y)" coordinate string
   - **Status**: Covered

#### Quarter 2

4. **Competency**: Measure and compare lengths of objects, in meters (m) or centimeters (cm), and distance in meters, using appropriate measuring tools.
   - **Content Area**: Measurement and Geometry
   - **Generator**: measurement
   - **Template Function**: `_gen_measurement()`
   - **Template Problem Example**: "Convert 5 meters to centimeters."
   - **Difficulty Dimensions**:
     - measurement_type: "length"
     - value_max: 10-10000
     - conversion_steps: 0-2
     - unit_familiarity: 0.0-0.5
     - computation_required: 0.5
   - **Visual Option**: No - Linear measurement requires physical tools
   - **Status**: Covered

   **MCQ Skeleton Details**:
   - **Sub-Generator**: `_gen_meas_unit_selection` (primary), also `_gen_meas_length_convert`, `_gen_meas_compare`
   - **Scope**: Measurement, comparison, and conversion of lengths in m/cm
   - **Stem Variations (unit selection)**:
     1. "Which unit is better for measuring the length of {obj}: meters or centimeters?"
     2. "To measure {obj}, should you use meters (m) or centimeters (cm)?"
     3. "The most appropriate unit for measuring {obj} is:"
   - **Stem Variations (conversion)**:
     4. "Convert {m} meters to centimeters."
     5. "How many centimeters are in {m} meters?"
     6. "{m} m = ___ cm"
   - **Stem Variations (comparison)**:
     7. "Which is longer: {a} cm or {b} m?"
     8. "Compare: {a} cm and {b} m. Which is greater?"
     9. "A ribbon is {a} cm long. A rope is {b} m long. Which is longer?"
   - **Traps**:
     | Code | Description |
     |------|-------------|
     | `ms_wrong_unit` | Chose the wrong unit for the object |
     | `ms_unit_too_big` | Used kilometers when cm was needed |
     | `ms_unit_too_small` | Used millimeters when m was needed |
     | `ms_wrong_factor` | Used ×10 instead of ×100 for m→cm |
     | `ms_no_convert` | Compared digits without converting units |
   - **Answer Format**: Unit name, integer string, or "{value} {unit}" string
   - **Status**: Covered

5. **Competency**: Identify and use the appropriate unit (m or cm) to measure the length of an object and the distance between two locations.
   - **Content Area**: Measurement and Geometry
   - **Generator**: measurement
   - **Template Problem Example**: "Which unit is better for measuring a pencil: meters or centimeters?"
   - **Visual Option**: No - Unit selection is conceptual
   - **Status**: Covered

   **MCQ Skeleton Details**:
   - **Sub-Generator**: `_gen_meas_unit_selection`
   - **Scope**: Selecting appropriate unit for real-world objects (same sub-generator as #4)
   - **Stem Variations**:
     1. "Which unit is better for measuring the length of {obj}: meters or centimeters?"
     2. "To measure {obj}, should you use meters (m) or centimeters (cm)?"
     3. "The most appropriate unit for measuring {obj} is:"
   - **Object Pool (cm)**: pencil (15cm), eraser (5cm), book (25cm), hand span (20cm), crayon (10cm), spoon (18cm)
   - **Object Pool (m)**: classroom (8m), swimming pool (25m), basketball court (28m), hallway (15m), flagpole (10m), school bus (12m)
   - **Traps**:
     | Code | Description |
     |------|-------------|
     | `ms_wrong_unit` | Chose the wrong unit |
     | `ms_unit_too_big` | kilometers |
     | `ms_unit_too_small` | millimeters |
   - **Answer Format**: "centimeters" or "meters"
   - **Status**: Covered

6. **Competency**: Estimate length using meters or centimeters, and distance using meters.
   - **Content Area**: Measurement and Geometry
   - **Generator**: measurement (estimation branch)
   - **Visual Option**: No
   - **Status**: Covered

   **MCQ Skeleton Details**:
   - **Sub-Generator**: `_gen_meas_estimation`
   - **Scope**: Estimate real-world lengths using appropriate units
   - **Stem Variations**:
     1. "Which is the best estimate for the length of {obj}?"
     2. "About how long is {obj}?"
     3. "Estimate: The length of {obj} is closest to:"
   - **Object Pool**: door's height (2m), pencil (18cm), classroom (10m), finger width (1cm), car (4m), table height (75cm), ant (3mm), basketball court (28m)
   - **Traps**:
     | Code | Description |
     |------|-------------|
     | `ms_est_too_high` | Overestimated by ×10 |
     | `ms_est_too_low` | Underestimated by ÷5 |
     | `ms_wrong_unit` | Gave value in wrong unit (e.g., "18 m" for a pencil) |
   - **Answer Format**: "about {value} {unit}" string
   - **Status**: Covered

7. **Competency**: Solve problems involving length and distance.
   - **Content Area**: Measurement and Geometry
   - **Generator**: measurement
   - **Visual Option**: No
   - **Status**: Covered

   **MCQ Skeleton Details**:
   - **Sub-Generator**: `_gen_meas_word_problem`
   - **Scope**: Addition and subtraction word problems with length/distance context
   - **Stem Variations (addition)**:
     1. "A path is {a} {unit} long. Another path is {b} {unit} long. What is the total distance?"
     2. "A piece of string is {a} {unit}. Another piece is {b} {unit}. How long are they together?"
     3. "You walk {a} {unit} then {b} {unit} more. How far did you walk in total?"
   - **Stem Variations (subtraction)**:
     4. "A rope is {total} {unit} long. You cut off {part} {unit}. How much is left?"
     5. "A board is {total} {unit}. After cutting {part} {unit}, what length remains?"
     6. "You have {total} {unit} of ribbon. You use {part} {unit}. How much is left?"
   - **Traps**:
     | Code | Description |
     |------|-------------|
     | `ms_wrong_op` | Added when should subtract, or vice versa |
     | `ms_off_by` | Off by 10 (arithmetic error) |
     | `ms_off_one` | Off by 1 |
     | `ms_partial` | Gave one operand instead of computing result |
   - **Answer Format**: Integer string (length value)
   - **Status**: Covered

#### Quarter 4

8. **Competency**: Describe the duration of an event in terms of number of days and/or weeks using a calendar.
   - **Content Area**: Measurement and Geometry
   - **Generator**: measurement (conceptual)
   - **Visual Option**: Yes - Calendar visual
   - **Status**: Partial

   **Visual Skeleton Details**:
   - **Visual Type**: Calendar
   - **Template Function**: `_gen_calendar()`
   - **Visual Params**:
     - `year`: Calendar year (e.g., 2024)
     - `month`: Month number (1-12)
     - `task_type`: "measure_duration" - Calculate days between dates
     - `correct_duration`: Number of days (inclusive count)
   - **Example Output**:
     ```json
     {
       "year": 2024,
       "month": 3,
       "task_type": "measure_duration",
       "correct_date": null,
       "correct_duration": 7
     }
     ```
     *Question: "How many days are there from 3/15 to 3/21, inclusive?"*
    - **Question Modes**: interactive (click start and end dates on calendar), mcq (select correct duration), fill_in (type the number of days)

   **MCQ Skeleton Details**:
   - **Sub-Generator**: `_gen_meas_time` (calendar duration mode)
   - **Scope**: Counting days between two named days of the week
   - **Stem Variations**:
     1. "How many days are there from {start_day} to {end_day}?"
     2. "An event starts on {start_day} and ends on {end_day}. How many days is that?"
     3. "Count the days from {start_day} to {end_day} (not including {start_day})."
   - **Traps**:
     | Code | Description |
     |------|-------------|
     | `ms_inclusive_count` | Counted start day (off by +1) |
     | `ms_off_one` | Off by one in either direction |
     | `ms_complement` | Gave 7 minus the correct answer |
   - **Answer Format**: Integer string (number of days)
   - **Status**: Covered

9. **Competency**: Read and write time in hours and minutes, with a.m. and p.m., using an analog clock.
   - **Content Area**: Measurement and Geometry
   - **Generator**: measurement (with visual fallback)
   - **Template Function**: `_gen_measurement()` → ClockSet visual
   - **Template Problem Example**: "[VISUAL] Show 3:30 PM on the clock."
   - **Visual Option**: Yes - ClockSet visual (REQUIRED)
   - **Status**: Covered

   **Visual Skeleton Details**:
   - **Visual Type**: ClockSet
   - **Template Function**: `_gen_clock_set()`
   - **Visual Params**:
     - `target_time`: Time string (e.g., "3:30" or "15:30")
     - `use_24_hour`: Boolean (false for Grade 2, true for Grade 5+)
     - `hours`: Hour value (1-12 or 0-23)
     - `minutes`: Minute value (0-59)
     - `display_hours`: Hour for clock face display (1-12)
     - `minute_angle`: Calculated angle for minute hand (0-360)
     - `hour_angle`: Calculated angle for hour hand (0-360)
     - `minute_snap_interval`: 5 (snap to 5-minute marks)
   - **Example Output**:
     ```json
     {
       "target_time": "3:30",
       "use_24_hour": false,
       "hours": 3,
       "minutes": 30,
       "display_hours": 3,
       "minute_angle": 180,
       "hour_angle": 105,
       "minute_snap_interval": 5
     }
     ```
     *Question: "Set the clock to show 3:30."*
    - **Question Modes**: interactive (drag clock hands), mcq (select correct clock from options), fill_in (type the time shown)

   **MCQ Skeleton Details**:
   - **Sub-Generator**: `_gen_meas_time` (general time facts mode)
   - **Scope**: MCQ fallback for time-telling — general time facts (visual ClockSet preferred)
   - **Stem Variations**:
     1. "How many minutes are in 1 hour?" → 60
     2. "How many hours are in 1 day?" → 24
     3. "How many days are in 1 week?" → 7
     4. "How many minutes are in 2 hours?" → 120
     5. "How many days are in 2 weeks?" → 14
   - **Traps**:
     | Code | Description |
     |------|-------------|
     | `ms_wrong_fact` | Wrong conversion factor |
     | `ms_half` | Gave half the correct value (12 for hours) |
     | `ms_confused_unit` | Mixed up unit types (gave 60 for hours question) |
   - **Answer Format**: Integer string
   - **Note**: Visual ClockSet mode is strongly preferred for this competency
   - **Status**: Covered

10. **Competency**: Solve problems involving elapsed time (minutes in an hour, hours in a day, days in a week), including timetables.
     - **Content Area**: Measurement and Geometry
     - **Generator**: measurement
     - **Visual Option**: Yes - ClockSet visual
     - **Status**: Partial

     **Visual Skeleton Details**:
     - **Visual Type**: ClockSet (for time-based elapsed time) or Calendar (for date-based)
     - **Template Function**: `_gen_clock_set()` or `_gen_calendar()`
     - **Visual Params (ClockSet)**:
       - `target_time`: End time
       - `start_time`: Beginning time for elapsed calculation
       - `hours`/`minutes`: End time values
       - `elapsed_minutes`: Correct answer duration
     - **Example Output (ClockSet)**:
       ```json
       {
         "target_time": "4:15",
         "start_time": "2:45",
         "hours": 4,
         "minutes": 15,
         "elapsed_minutes": 90
       }
       ```
       *Question: "How much time passed from 2:45 to 4:15?"*
      - **Question Modes**: interactive (use clock to calculate), mcq (select correct duration), fill_in (type elapsed time)

      **MCQ Skeleton Details**:
      - **Sub-Generator**: `_gen_meas_time` (elapsed time mode)
      - **Scope**: Elapsed time word problems — given start time and duration, find end time
      - **Stem Variations**:
        1. "A movie starts at {start_time} and lasts {elapsed} minutes. When does it end?"
        2. "You begin reading at {start_time}. After {elapsed} minutes, what time is it?"
        3. "Class starts at {start_time} and is {elapsed} minutes long. What time does it end?"
      - **Also includes general facts**:
        4. "How many minutes are in 1 hour?" → 60
        5. "How many hours are in 1 day?" → 24
        6. "How many days are in 1 week?" → 7
      - **Variables**: start_h (1-10), start_m (0/15/30/45), elapsed_min (15/30/45/60/90/120)
      - **Traps**:
        | Code | Description |
        |------|-------------|
        | `ms_time_no_min` | Added elapsed minutes to hours directly |
        | `ms_time_no_carry` | Didn't carry when minutes exceed 60 |
        | `ms_off_five_min` | Off by 5 minutes |
        | `ms_wrong_fact` | Wrong time conversion fact |
      - **Answer Format**: Time string "H:MM" or integer string
      - **Status**: Covered

11. **Competency**: Identify and explain the difference between straight and curved lines, and flat and curved surfaces of 3-dimensional objects.
     - **Content Area**: Measurement and Geometry
     - **Generator**: geometry_props
     - **Visual Option**: Yes - Categorize visual
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: Categorize
     - **Template Function**: `_gen_categorize()`
     - **Visual Params**:
       - `categories`: ["Straight Lines", "Curved Lines"] or ["Flat Surfaces", "Curved Surfaces"]
       - `items`: List of line segments or 3D object images/names
       - `correct_categories`: Mapping of items to their line/surface type
     - **Example Output**:
       ```json
       {
         "categories": ["Straight Lines", "Curved Lines"],
         "items": ["Side of a book", "Edge of a coin", "Ruler edge", "Plate rim", "Door frame", "Ball edge"],
         "correct_categories": {
           "Side of a book": "Straight Lines",
           "Edge of a coin": "Curved Lines",
           "Ruler edge": "Straight Lines",
           "Plate rim": "Curved Lines",
           "Door frame": "Straight Lines",
           "Ball edge": "Curved Lines"
         }
       }
       ```
      - **Question Modes**: interactive (drag items to categories), mcq (select category for given item), fill_in (type the classification)

      **MCQ Skeleton Details**:
      - **Sub-Generator**: `_gen_geo_surfaces`
      - **Scope**: Identify straight vs curved lines, flat vs curved surfaces of 3D objects
      - **Stem Variations** (8 question templates, 3 stems each):
        1. "How many flat surfaces does a sphere (ball) have?" → 0
        2. "A ball has ___ flat surface(s)." → 0
        3. "Count the flat faces of a sphere." → 0
        4. "How many flat surfaces does a cylinder (can) have?" → 2
        5. "A can has ___ flat surface(s)." → 2
        6. "Count the flat faces of a cylinder." → 2
        7. "How many curved surfaces does a cylinder have?" → 1
        8. "A cylinder has ___ curved surface(s)." → 1
        9. "Count the curved faces of a can." → 1
        10. "How many curved surfaces does a cube have?" → 0
        11. "A cube (like a box) has ___ curved surface(s)." → 0
        12. "Does a cube have any curved faces?" → 0
        13. "A cone has how many flat surface(s)?" → 1
        14. "Count the flat faces of a cone." → 1
        15. "How many flat surfaces does an ice cream cone shape have?" → 1
        16. "Which 3D shape has ONLY flat surfaces?" → cube
        17. "Which solid has no curved surfaces at all?" → cube
        18. "Identify the shape with only flat faces:" → cube
        19. "The edge of a coin is an example of a:" → curved line
        20. "The rim of a plate shows a:" → curved line
        21. "The outline of a wheel is a:" → curved line
        22. "The edge of a ruler is an example of a:" → straight line
        23. "The side of a book shows a:" → straight line
        24. "A door frame contains examples of:" → straight line
      - **Traps**:
        | Code | Description |
        |------|-------------|
        | `gp_one_face` | Said sphere has 1 flat face |
        | `gp_forgot_bottom` | Forgot bottom flat face of cylinder (said 1 instead of 2) |
        | `gp_only_curved` | Said cylinder has 0 flat faces |
        | `gp_counted_flat` | Counted flat surfaces when asked about curved |
        | `gp_forgot_curved` | Forgot the curved surface exists |
        | `gp_wrong_type` | Confused straight line with curved or vice versa |
        | `gp_confused_2d_3d` | Confused 2D line concepts with 3D surface concepts |
      - **Answer Format**: Integer string or descriptive string
      - **Status**: Covered

12. **Competency**: Identify and measure the perimeter of a plane figure using appropriate tools.
     - **Content Area**: Measurement and Geometry
     - **Generator**: measurement
     - **Visual Option**: Yes - GridArea visual
     - **Status**: Partial

     **Visual Skeleton Details**:
     - **Visual Type**: GridArea
     - **Template Function**: `_gen_grid_area()`
     - **Visual Params**:
       - `grid_size`: [10, 10] - Grid dimensions
       - `shape_type`: "rectangle" or "polygon"
       - `width`: Shape width in grid units
       - `height`: Shape height in grid units
       - `correct_count`: Perimeter (2 × (width + height))
       - `measure_type`: "perimeter" vs "area"
     - **Example Output**:
       ```json
       {
         "grid_size": [10, 10],
         "shape_type": "rectangle",
         "width": 5,
         "height": 3,
         "correct_count": 16,
         "measure_type": "perimeter"
       }
       ```
        *Question: "Count the units around the outside of the rectangle. What is the perimeter?"*
      - **Question Modes**: interactive (count/grid outline), mcq (select correct perimeter), fill_in (type the perimeter value)

      **MCQ Skeleton Details**:
      - **Sub-Generator**: `_gen_meas_perimeter`
      - **Scope**: Perimeter of squares and rectangles (Grade 2 basic measurement)
      - **Stem Variations (square)**:
        1. "Find the perimeter of a square with side length {s} cm."
        2. "A square has sides of {s} cm each. What is its perimeter?"
        3. "What is the perimeter of a square with side = {s} cm?"
      - **Stem Variations (rectangle)**:
        4. "Find the perimeter of a rectangle with length {l} cm and width {w} cm."
        5. "A rectangle is {l} cm long and {w} cm wide. What is its perimeter?"
        6. "What is the perimeter of a rectangle: L = {l} cm, W = {w} cm?"
      - **Traps**:
        | Code | Description |
        |------|-------------|
        | `ms_used_area` | Used area formula (L×W) instead of 2(L+W) |
        | `ms_only_once` | Only added L+W once without doubling |
        | `ms_only_two_sides` | Only counted 2 sides of 4 |
        | `ms_extra_side` | Added perimeter + extra side |
      - **Answer Format**: Integer string (perimeter in cm)
      - **Status**: Covered

13. **Competency**: Find the perimeter of triangles, squares, and rectangles.
     - **Content Area**: Measurement and Geometry
     - **Generator**: measurement
     - **Visual Option**: Yes - GridArea visual
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: GridArea
     - **Template Function**: `_gen_grid_area()`
     - **Visual Params**:
       - `grid_size`: [10, 10] - Grid dimensions
       - `shape_type`: "rectangle", "square", or "triangle"
       - `width`: Width in grid units (for rectangles/squares)
       - `height`: Height in grid units
       - `correct_count`: Perimeter value
       - `sides`: Array of side lengths (for triangles)
     - **Example Output (Rectangle)**:
       ```json
       {
         "grid_size": [10, 10],
         "shape_type": "rectangle",
         "width": 4,
         "height": 6,
         "correct_count": 20,
         "sides": null
       }
       ```
     - **Example Output (Triangle)**:
       ```json
       {
         "grid_size": [10, 10],
         "shape_type": "triangle",
         "width": null,
         "height": null,
         "correct_count": 12,
         "sides": [3, 4, 5]
       }
       ```
      - **Question Modes**: interactive (trace perimeter on grid), mcq (select correct perimeter), fill_in (type perimeter)

      **MCQ Skeleton Details**:
      - **Sub-Generator**: `_gen_meas_perimeter`
      - **Scope**: All shapes — square, rectangle, AND triangle perimeter
      - **Stem Variations (square)**:
        1. "Find the perimeter of a square with side length {s} cm."
        2. "A square has sides of {s} cm each. What is its perimeter?"
        3. "What is the perimeter of a square with side = {s} cm?"
      - **Stem Variations (rectangle)**:
        4. "Find the perimeter of a rectangle with length {l} cm and width {w} cm."
        5. "A rectangle is {l} cm long and {w} cm wide. What is its perimeter?"
        6. "What is the perimeter of a rectangle: L = {l} cm, W = {w} cm?"
      - **Stem Variations (triangle)**:
        7. "A triangle has sides of {a} cm, {b} cm, and {c} cm. What is its perimeter?"
        8. "Find the perimeter of a triangle with sides {a}, {b}, and {c} cm."
        9. "The sides of a triangle measure {a} cm, {b} cm, and {c} cm. Perimeter = ?"
      - **Note**: Triangle sides generated as valid triangles (sum of any two > third)
      - **Traps**:
        | Code | Description |
        |------|-------------|
        | `ms_used_area` | Used L×W (area formula) instead of perimeter |
        | `ms_only_once` | Added L+W only once for rectangle |
        | `ms_forgot_side` | Only added 2 of 3 triangle sides |
        | `ms_counted_extra` | Added perimeter + one extra side |
        | `ms_used_max_side` | Multiplied largest side by 3 |
      - **Answer Format**: Integer string (perimeter value)
      - **Status**: Covered

14. **Competency**: Solve problems involving perimeter of triangles, squares, and rectangles.
     - **Content Area**: Measurement and Geometry
     - **Generator**: measurement
     - **Visual Option**: Yes - GridArea
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: GridArea
     - **Template Function**: `_gen_grid_area()`
     - **Visual Params**:
       - `grid_size`: [10, 10] - Grid dimensions
       - `shape_type`: "rectangle", "square", or "triangle"
       - `width`: Width in grid units
       - `height`: Height in grid units
       - `correct_count`: Perimeter or missing side length
       - `problem_type`: "find_perimeter", "find_missing_side"
     - **Example Output (Find missing side)**:
       ```json
       {
         "grid_size": [10, 10],
         "shape_type": "rectangle",
         "width": 5,
         "height": null,
         "correct_count": 3,
         "problem_type": "find_missing_side",
         "given_perimeter": 16
       }
       ```
        *Question: "A rectangle has perimeter 16 and one side is 5. Find the other side."*
      - **Question Modes**: interactive (manipulate grid), mcq (select answer), fill_in (type the missing value)

      **MCQ Skeleton Details**:
      - **Sub-Generator**: `_gen_meas_perimeter` (missing side mode)
      - **Scope**: Perimeter word problems — find perimeter OR find missing side given perimeter
      - **Stem Variations (find perimeter)**:
        1. "Find the perimeter of a square with side length {s} cm."
        2. "A rectangle is {l} cm long and {w} cm wide. What is its perimeter?"
        3. "A triangle has sides of {a} cm, {b} cm, and {c} cm. What is its perimeter?"
      - **Stem Variations (find missing side)**:
        4. "A square has a perimeter of {p} cm. What is the length of one side?"
        5. "The perimeter of a square is {p} cm. Find the side length."
        6. "If a square's perimeter is {p} cm, each side measures ___ cm."
        7. "A rectangle has a perimeter of {p} cm and a length of {l} cm. Find the width."
        8. "The perimeter of a rectangle is {p} cm. One side is {l} cm. What is the other side?"
        9. "Perimeter = {p} cm, length = {l} cm. Width = ?"
      - **Traps (find perimeter)**: `ms_used_area`, `ms_only_once`, `ms_forgot_side`
      - **Traps (find missing side)**:
        | Code | Description |
        |------|-------------|
        | `ms_forgot_double` | Subtracted length once instead of twice from half-perimeter |
        | `ms_half_perim` | Gave half the perimeter without further computation |
        | `ms_div_by_2` | Divided perimeter by 2 (correct for half-perim, not for side) |
        | `ms_no_divide` | Gave the perimeter unchanged |
        | `ms_off_one` | Off by one |
      - **Answer Format**: Integer string (perimeter or side length)
      - **Status**: Covered

### Number and Algebra

#### Quarter 1

15. **Competency**: Count up to 1000.
     - **Generator**: counting
     - **Template Functions**: `_gen_counting_after()`, `_gen_counting_before()`, `_gen_counting_skip()`
     - **Example**: "What number comes after 847?"
     - **Dimensions**: max_number: 1000, skip_interval: [1,2,5,10,20,50,100]
     - **Visual Option**: Yes - NumberLine
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: NumberLine
     - **Template Function**: `_gen_number_line()`
     - **Visual Params**:
       - `value`: Target number to locate (1-999)
       - `range`: [0, max_val] - Number line bounds
       - `divisions`: Number of tick marks
       - `content_type`: "whole_number"
       - `correct_position`: Index position of the value
       - `labels`: ["0", "max_val"] - Endpoint labels
       - `is_interactive`: true
     - **Example Output**:
       ```json
       {
         "value": 847,
         "range": [0, 1000],
         "divisions": 1000,
         "content_type": "whole_number",
         "correct_position": 847,
         "labels": ["0", "1000"],
         "is_interactive": true
       }
       ```
       *Question: "Move the dot to show 847 on the number line."*
     - **Question Modes**: interactive (drag dot to position), mcq (select marked position), fill_in (type the value at a position)

16. **Competency**: Read and write numerals up to 1000.
    - **Generator**: place_value
    - **Example**: "Write 'three hundred twenty-five' as a numeral."
    - **Dimensions**: digit_count: 3, question_type: 0.0-0.3
    - **Visual Option**: No
    - **Status**: Partial

17. **Competency**: Recognize and represent numbers up to 1000 using models and numerals.
     - **Generator**: place_value
     - **Example**: "In 725, what digit is in the tens place?"
     - **Dimensions**: digit_count: 3, target_place: 0-2
     - **Visual Option**: Yes - NumberLine
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: NumberLine
     - **Template Function**: `_gen_number_line()`
     - **Visual Params**:
       - `value`: Target number (1-999)
       - `range`: [0, 100] or [0, 1000] - Appropriate scale
       - `divisions`: Tick mark divisions
       - `content_type`: "whole_number"
       - `correct_position`: Position index
       - `labels`: Endpoint labels
       - `is_interactive`: true
     - **Example Output**:
       ```json
       {
         "value": 725,
         "range": [0, 1000],
         "divisions": 100,
         "content_type": "whole_number",
         "correct_position": 72.5,
         "labels": ["0", "1000"],
         "is_interactive": true
       }
       ```
       *Question: "Show where 725 belongs on the number line."*
     - **Question Modes**: interactive (place marker), mcq (select position), fill_in (read position)

18. **Competency**: Count by 2s, 5s, 10s, 20s, 50s, and 100s (not beyond 1000).
     - **Generator**: counting
     - **Example**: "What comes next? 200, 250, 300, ___"
     - **Dimensions**: max_number: 1000, skip_interval: [2,5,10,20,50,100]
     - **Visual Option**: Yes - NumberLine
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: NumberLine
     - **Template Function**: `_gen_number_line()`
     - **Visual Params**:
       - `value`: Target number in skip sequence
       - `range`: [0, 1000]
       - `divisions`: Spaced by skip_interval (e.g., 100 for counting by 10s to 1000)
       - `content_type`: "whole_number"
       - `skip_interval`: 2, 5, 10, 20, 50, or 100
       - `correct_position`: Position index
     - **Example Output (Counting by 50s)**:
       ```json
       {
         "value": 350,
         "range": [0, 1000],
         "divisions": 20,
         "content_type": "whole_number",
         "skip_interval": 50,
         "correct_position": 7,
         "labels": ["0", "1000"],
         "is_interactive": true
       }
       ```
       *Question: "Mark the next number when counting by 50s from 300."*
     - **Question Modes**: interactive (mark position), mcq (select from options), fill_in (type the next number)

19. **Competency**: Order numbers up to 1000 from smallest to largest, and vice versa.
     - **Generator**: compare_order
     - **Example**: "Which number is greater: 456 or 564?"
     - **Visual Option**: Yes - SortOrder visual
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: SortOrder
     - **Template Function**: `_gen_sort_order()`
     - **Visual Params**:
       - `items`: Array of numbers to sort (3-5 numbers, 1-1000 range)
       - `correct_sequence`: Sorted array (ascending or descending)
       - `direction`: "ascending" or "descending"
     - **Example Output**:
       ```json
       {
         "items": [456, 128, 702, 389],
         "correct_sequence": [128, 389, 456, 702],
         "direction": "ascending"
       }
       ```
       *Question: "Arrange the numbers from smallest to largest."*
     - **Question Modes**: interactive (drag to reorder), mcq (select correct order), fill_in (type the sequence)

20. **Competency**: Describe the position of objects using ordinal numbers up to 20th.
    - **Generator**: counting
    - **Template Function**: `_gen_counting_ordinal()`
    - **Example**: "In a row of fruits, what is the 15th item?"
    - **Dimensions**: ordinal_max: 20
    - **Visual Option**: No
    - **Status**: Covered

21. **Competency**: Determine the place value of a digit in a 3-digit number, the value of a digit, and the digit of a number, given its place value.
     - **Generator**: place_value
     - **Template Functions**: `_gen_pv_digit()`, `_gen_pv_value()`
     - **Example**: "In 847, what is the VALUE of the digit 4?" (Answer: 40)
     - **Dimensions**: digit_count: 3, target_place: 0-2, question_type: 0.0-0.5
     - **Visual Option**: Yes - FillInTable
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: FillInTable
     - **Template Function**: `_gen_fill_in_table()`
     - **Visual Params**:
       - `columns`: ["Number", "Hundreds", "Tens", "Ones"]
       - `rows`: Table rows with some cells blank
       - `blank_inputs`: Indices of cells to fill
       - `correct_fills`: Correct values for blank cells
       - `pattern_type`: "place_value"
     - **Example Output**:
       ```json
       {
         "columns": ["Number", "Hundreds", "Tens", "Ones"],
         "rows": [
           [847, 8, null, 7],
           [562, null, 6, 2],
           [935, 9, 3, null]
         ],
         "blank_inputs": [1, 2, 3],
         "correct_fills": [4, 5, 5],
         "pattern_type": "place_value"
       }
       ```
       *Question: "Complete the place value table."*
     - **Question Modes**: interactive (fill in blanks), mcq (select correct values), fill_in (type each value)

22. **Competency**: Illustrate addition of 2-digit and 1-digit numbers as 'counting up' on the number line.
     - **Generator**: arithmetic
     - **Example**: "45 + 7 = ?"
     - **Dimensions**: operand_max: 100, regrouping_probability: 0.5
     - **Visual Option**: Yes - NumberLine
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: NumberLine
     - **Template Function**: `_gen_number_line()`
     - **Visual Params**:
       - `start_value`: Starting number (e.g., 45)
       - `addend`: Number to add (e.g., 7)
       - `range`: [0, 100] - Appropriate bounds
       - `divisions`: Tick divisions
       - `content_type`: "addition_visualization"
       - `correct_position`: Final position (start + addend)
       - `show_jumps`: true - Show counting up steps
     - **Example Output**:
       ```json
       {
         "start_value": 45,
         "addend": 7,
         "range": [0, 100],
         "divisions": 100,
         "content_type": "addition_visualization",
         "correct_position": 52,
         "show_jumps": true,
         "jump_size": 1,
         "labels": ["0", "100"],
         "is_interactive": true
       }
       ```
       *Question: "Show 45 + 7 by making jumps on the number line."*
     - **Question Modes**: interactive (make jumps to add), mcq (select final position), fill_in (type the sum)

23. **Competency**: Add numbers with sums up to 1000 in expanded form.
    - **Generator**: arithmetic
    - **Example**: "300 + 40 + 5 + 200 + 30 + 7 = ?"
    - **Dimensions**: operand_max: 1000, step_count: 2-3
    - **Visual Option**: No
    - **Status**: Covered

24. **Competency**: Add numbers with sums up to 1000, with or without regrouping.
    - **Generator**: arithmetic
    - **Example**: "458 + 376 = ?"
    - **Dimensions**: operand_max: 1000, regrouping_probability: 0.0-1.0
    - **Visual Option**: No
    - **Status**: Covered

25. **Competency**: Illustrate and apply properties of addition using sums up to 1000.
    - **Generator**: arithmetic (conceptual)
    - **Example**: "Which shows the commutative property: 5+3=3+5?"
    - **Dimensions**: abstraction_level: 0.6
    - **Visual Option**: No
    - **Status**: Partial

#### Quarter 2

26. **Competency**: Determine and write the value of a number of bills, or a number of coins, or a combination of bills and coins up to 1000.
     - **Generator**: arithmetic (money context)
     - **Example**: "What is the value of 2 100 bills, 1 50 bill, and 3 5 coins?"
     - **Dimensions**: operand_max: 1000, step_count: 2-3
     - **Visual Option**: Yes - PesoMoney visual
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: PesoMoney
     - **Template Function**: `_gen_peso_money()`
     - **Visual Params**:
       - `target_amount`: Amount to make (e.g., 365)
       - `available_denominations`: [1, 5, 10, 20, 50, 100, 200, 500, 1000] - Philippine currency
       - `greedy_solution`: One valid combination
       - `require_fewest`: Boolean - Whether to require optimal solution
       - `difficulty_scalar`: 0.0-1.2 - Difficulty factor
     - **Example Output**:
       ```json
       {
         "target_amount": 365,
         "available_denominations": [1, 5, 10, 20, 50, 100, 200, 500],
         "greedy_solution": [200, 100, 50, 10, 5],
         "require_fewest": false,
         "difficulty_scalar": 0.5
       }
       ```
       *Question: "Use coins and bills to make exactly ₱365."*
     - **Question Modes**: interactive (drag coins/bills), mcq (select correct combination), fill_in (type total value)

27. **Competency**: Compare the values of different denominations of peso coins and bills up to 1000.
     - **Generator**: compare_order
     - **Example**: "Which has more value: 5 20 coins or 1 100 bill?"
     - **Visual Option**: Yes - PesoMoney
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: PesoMoney
     - **Template Function**: `_gen_peso_money()`
     - **Visual Params**:
       - `target_amount`: Comparison amounts (e.g., two sets)
       - `option_a`: First combination of denominations
       - `option_b`: Second combination of denominations
       - `correct_answer`: "A", "B", or "equal"
     - **Example Output**:
       ```json
       {
         "option_a": {"denominations": [20, 20, 20, 20, 20], "total": 100},
         "option_b": {"denominations": [100], "total": 100},
         "target_amount": null,
         "comparison_mode": true,
         "correct_answer": "equal"
       }
       ```
       *Question: "Which set has more value: 5 ₱20 coins or 1 ₱100 bill?"*
     - **Question Modes**: interactive (compare visible sets), mcq (select A, B, or equal), fill_in (type which is greater)

28. **Competency**: Solve problems involving addition with sums up to 1000, including problems involving money.
     - **Generator**: arithmetic
     - **Example**: "Mara has 250. She earns 175 more. How much does she have now?"
     - **Visual Option**: Yes - PesoMoney
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: PesoMoney
     - **Template Function**: `_gen_peso_money()`
     - **Visual Params**:
       - `problem_type`: "addition"
       - `starting_amount`: Initial amount (e.g., 250)
       - `amount_added`: Amount to add (e.g., 175)
       - `target_amount`: Correct sum (425)
       - `available_denominations`: Currency options for making the sum
     - **Example Output**:
       ```json
       {
         "problem_type": "addition",
         "starting_amount": 250,
         "amount_added": 175,
         "target_amount": 425,
         "available_denominations": [1, 5, 10, 20, 50, 100, 200],
         "show_as_transaction": true
       }
       ```
       *Question: "Mara has ₱250. She earns ₱175 more. Show ₱425 using bills and coins."*
     - **Question Modes**: interactive (drag money to represent total), mcq (select correct total), fill_in (type the sum)

29. **Competency**: Illustrate subtraction of 2-digit by 1-digit on the number line and as an inverse of addition.
     - **Generator**: arithmetic
     - **Example**: "58 - 7 = ?"
     - **Visual Option**: Yes - NumberLine
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: NumberLine
     - **Template Function**: `_gen_number_line()`
     - **Visual Params**:
       - `start_value`: Starting number (minuend, e.g., 58)
       - `subtrahend`: Number to subtract (e.g., 7)
       - `range`: [0, 100]
       - `divisions`: Tick divisions
       - `content_type`: "subtraction_visualization"
       - `correct_position`: Final position (start - subtrahend)
       - `show_jumps`: true - Show counting back steps
       - `jump_direction`: "backward"
     - **Example Output**:
       ```json
       {
         "start_value": 58,
         "subtrahend": 7,
         "range": [0, 100],
         "divisions": 100,
         "content_type": "subtraction_visualization",
         "correct_position": 51,
         "show_jumps": true,
         "jump_direction": "backward",
         "jump_size": 1,
         "labels": ["0", "100"],
         "is_interactive": true
       }
       ```
       *Question: "Show 58 - 7 by counting back on the number line."*
     - **Question Modes**: interactive (make backward jumps), mcq (select final position), fill_in (type the difference)

30. **Competency**: Subtract numbers where both numbers are less than 100 with regrouping.
    - **Generator**: arithmetic
    - **Example**: "73 - 28 = ?"
    - **Dimensions**: operand_max: 100, regrouping_required: True
    - **Visual Option**: No
    - **Status**: Covered

31. **Competency**: Solve problems involving subtraction where both numbers are less than 100.
    - **Generator**: arithmetic
    - **Example**: "There are 65 apples. 27 are eaten. How many remain?"
    - **Status**: Covered

32. **Competency**: Subtract numbers, where both numbers are less than 1000, with and without regrouping.
    - **Generator**: arithmetic
    - **Example**: "824 - 567 = ?"
    - **Dimensions**: operand_max: 1000
    - **Status**: Covered

33. **Competency**: Solve 1- and 2-step problems involving subtraction where both numbers are less than 1000.
     - **Generator**: arithmetic
     - **Example**: "A toy costs 450. You have 325. How much more do you need?"
     - **Visual Option**: Yes - PesoMoney
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: PesoMoney
     - **Template Function**: `_gen_peso_money()`
     - **Visual Params**:
       - `problem_type`: "subtraction"
       - `total_needed`: Target amount (e.g., 450)
       - `amount_have`: Starting amount (e.g., 325)
       - `target_amount`: Difference needed (125)
       - `show_comparison`: true - Show both amounts visually
     - **Example Output**:
       ```json
       {
         "problem_type": "subtraction",
         "total_needed": 450,
         "amount_have": 325,
         "target_amount": 125,
         "available_denominations": [1, 5, 10, 20, 50, 100],
         "show_comparison": true
       }
       ```
       *Question: "A toy costs ₱450. You have ₱325. How much more do you need? Show ₱125."*
     - **Question Modes**: interactive (show difference amount), mcq (select correct difference), fill_in (type the amount needed)

34. **Competency**: Determine the next term/s in increasing or decreasing patterns.
     - **Generator**: counting
     - **Example**: "What comes next? 150, 140, 130, ___"
     - **Dimensions**: direction_complexity: 1.0
     - **Visual Option**: Yes - RuleDiscovery visual
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: RuleDiscovery
     - **Template Function**: `_gen_rule_discovery()`
     - **Visual Params**:
       - `table`: Array of (n, output) pairs showing the pattern
       - `rule_expression`: Mathematical rule as string (e.g., "n*10-10" or "160-10*n")
       - `variable_name`: "n" (the input variable)
       - `pattern_type`: "linear" or "arithmetic"
     - **Example Output**:
       ```json
       {
         "table": [[1, 150], [2, 140], [3, 130], [4, 120]],
         "rule_expression": "160-10*n",
         "variable_name": "n",
         "pattern_type": "linear"
       }
       ```
       *Question: "What is the rule? Write it in terms of n. Then find the next term."*
     - **Question Modes**: interactive (complete pattern table), mcq (select rule), fill_in (type the next term or rule)

35. **Competency**: Create increasing or decreasing patterns.
     - **Generator**: counting
     - **Example**: "Continue the pattern: 5, 10, 15, ___, ___, ___"
     - **Visual Option**: Yes - FillInTable or RuleDiscovery
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: FillInTable
     - **Template Function**: `_gen_fill_in_table()`
     - **Visual Params**:
       - `columns`: ["Position", "Value"]
       - `rows`: Table rows with blanks for continuation
       - `blank_inputs`: Positions needing values
       - `correct_fills`: Values to complete the pattern
       - `rule_description`: Human-readable rule
       - `pattern_type`: "skip_count" or "repeating"
     - **Example Output**:
       ```json
       {
         "columns": ["Position", "Value"],
         "rows": [[1, 5], [2, 10], [3, 15], [4, null], [5, null], [6, null]],
         "blank_inputs": [4, 5, 6],
         "correct_fills": [20, 25, 30],
         "rule_description": "Add 5 each time",
         "pattern_type": "skip_count"
       }
       ```
       *Question: "Complete the table. Add 5 each time."*
     - **Question Modes**: interactive (fill in the blanks), mcq (select correct continuation), fill_in (type next values)

#### Quarter 3

36. **Competency**: Count the number of concrete objects in a group by repeated addition.
     - **Generator**: arithmetic
     - **Example**: "How many in 4 groups of 6?" (4 x 6 = 24)
     - **Visual Option**: Yes - GridArea visual
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: GridArea
     - **Template Function**: `_gen_grid_area()`
     - **Visual Params**:
       - `grid_size`: Array dimensions [rows, cols]
       - `shape_type`: "array"
       - `rows`: Number of groups (e.g., 4)
       - `columns`: Objects per group (e.g., 6)
       - `correct_count`: Total count (rows × columns)
       - `show_groups`: true - Visually group the array
     - **Example Output**:
       ```json
       {
         "grid_size": [4, 6],
         "shape_type": "array",
         "rows": 4,
         "columns": 6,
         "correct_count": 24,
         "show_groups": true,
         "group_label": "groups of 6"
       }
       ```
       *Question: "How many objects are there in 4 groups of 6? Count them."*
     - **Question Modes**: interactive (count objects on grid), mcq (select total), fill_in (type the total count)

37. **Competency**: Illustrate and write multiplication as repeated addition.
     - **Generator**: arithmetic
     - **Example**: "6 + 6 + 6 + 6 = ? (4 groups of 6)"
     - **Visual Option**: Yes - NumberLine
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: NumberLine
     - **Template Function**: `_gen_number_line()`
     - **Visual Params**:
       - `multiplicand`: Number being added repeatedly (e.g., 6)
       - `multiplier`: How many times to add it (e.g., 4)
       - `range`: [0, product + padding]
       - `content_type`: "repeated_addition"
       - `correct_position`: Final sum (24)
       - `show_jumps`: true - Show each addition as a jump
       - `jump_size`: Size of each jump (6)
     - **Example Output**:
       ```json
       {
         "multiplicand": 6,
         "multiplier": 4,
         "range": [0, 30],
         "content_type": "repeated_addition",
         "correct_position": 24,
         "show_jumps": true,
         "jump_size": 6,
         "jump_count": 4,
         "labels": ["0", "30"],
         "is_interactive": true
       }
       ```
       *Question: "Show 4 × 6 as jumps of 6 on the number line."*
     - **Question Modes**: interactive (make repeated jumps), mcq (select final position), fill_in (type the product)

38. **Competency**: Multiply numbers using the 2, 3, 4, 5, and 10 multiplication tables.
    - **Generator**: arithmetic
    - **Example**: "7 x 5 = ?"
    - **Dimensions**: operand_max: 100
    - **Status**: Covered

39. **Competency**: Solve multiplication problems using the 2, 3, 4, 5, and 10 multiplication tables.
     - **Generator**: arithmetic
     - **Example**: "If one pencil costs 5, how much do 8 pencils cost?"
     - **Visual Option**: Yes - PesoMoney
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: PesoMoney
     - **Template Function**: `_gen_peso_money()`
     - **Visual Params**:
       - `problem_type`: "multiplication"
       - `unit_price`: Price per item (e.g., 5)
       - `quantity`: Number of items (e.g., 8)
       - `target_amount`: Total cost (40)
       - `item_name`: Context item (e.g., "pencils")
     - **Example Output**:
       ```json
       {
         "problem_type": "multiplication",
         "unit_price": 5,
         "quantity": 8,
         "target_amount": 40,
         "item_name": "pencils",
         "available_denominations": [1, 5, 10, 20],
         "show_quantity": true
       }
       ```
       *Question: "If one pencil costs ₱5, how much do 8 pencils cost? Show ₱40."*
     - **Question Modes**: interactive (make total amount), mcq (select correct total), fill_in (type the cost)

40. **Competency**: Illustrate division through equal distribution.
     - **Generator**: arithmetic
     - **Example**: "Share 24 cookies equally among 6 friends."
     - **Visual Option**: Yes - GridArea visual
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: GridArea
     - **Template Function**: `_gen_grid_area()`
     - **Visual Params**:
       - `total_objects`: Total items to distribute (e.g., 24)
       - `num_groups`: Number of equal groups (e.g., 6)
       - `objects_per_group`: Result (4)
       - `shape_type`: "distribution_grid"
       - `grid_size`: [6, 4] - Groups × items per group
       - `correct_count`: Items per group
     - **Example Output**:
       ```json
       {
         "total_objects": 24,
         "num_groups": 6,
         "objects_per_group": 4,
         "shape_type": "distribution_grid",
         "grid_size": [6, 4],
         "correct_count": 4,
         "show_groups": true,
         "group_labels": ["Friend 1", "Friend 2", "Friend 3", "Friend 4", "Friend 5", "Friend 6"]
       }
       ```
       *Question: "Share 24 cookies equally among 6 friends. How many per friend?"*
     - **Question Modes**: interactive (distribute objects to groups), mcq (select amount per group), fill_in (type the quotient)

41. **Competency**: Illustrate and write division expressions using models.
     - **Generator**: arithmetic
     - **Example**: "24 / 6 = ?"
     - **Visual Option**: Yes - GridArea visual
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: GridArea
     - **Template Function**: `_gen_grid_area()`
     - **Visual Params**:
       - `dividend`: Total items (24)
       - `divisor`: Group size or number of groups (6)
       - `correct_count`: Quotient (4)
       - `shape_type`: "division_model"
       - `division_type`: "partition" (equal groups) or "measurement" (group size)
       - `grid_size`: [6, 4]
     - **Example Output**:
       ```json
       {
         "dividend": 24,
         "divisor": 6,
         "correct_count": 4,
         "shape_type": "division_model",
         "division_type": "partition",
         "grid_size": [6, 4],
         "visualization_mode": "array"
       }
       ```
       *Question: "24 ÷ 6 = ? Circle groups of 6 to find the answer."*
     - **Question Modes**: interactive (circle groups on grid), mcq (select answer), fill_in (type the quotient)

42. **Competency**: Divide numbers using the 2, 3, 4, 5, and 10 multiplication tables.
    - **Generator**: arithmetic
    - **Example**: "35 / 5 = ?"
    - **Status**: Covered

43. **Competency**: Find the missing number in a number sentence involving multiplication or division.
    - **Generator**: arithmetic
    - **Example**: "6 x ___ = 42"
    - **Status**: Covered

44. **Competency**: Distinguish even and odd numbers using division by 2.
    - **Generator**: conceptual
    - **Example**: "Is 24 even or odd?"
    - **Status**: Covered

45. **Competency**: Solve division problems using the 2, 3, 4, 5, and 10 multiplication tables.
     - **Generator**: arithmetic
     - **Example**: "60 is shared equally among 5 children."
     - **Visual Option**: Yes - PesoMoney
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: PesoMoney
     - **Template Function**: `_gen_peso_money()`
     - **Visual Params**:
       - `problem_type`: "division"
       - `total_amount`: Amount to share (60)
       - `num_people`: Number of recipients (5)
       - `target_amount`: Amount per person (12)
       - `denominations`: Available bills/coins for division
     - **Example Output**:
       ```json
       {
         "problem_type": "division",
         "total_amount": 60,
         "num_people": 5,
         "target_amount": 12,
         "available_denominations": [1, 5, 10, 20, 50],
         "show_sharing": true
       }
       ```
       *Question: "₱60 is shared equally among 5 children. How much does each get?"*
     - **Question Modes**: interactive (distribute money equally), mcq (select amount per person), fill_in (type the quotient)

#### Quarter 4

46. **Competency**: Represent and identify unit fractions with denominators 2, 3, 4, 5, 6, and 8.
     - **Generator**: fractions
     - **Example**: "A pizza is cut into 6 equal slices. If 1 slice is eaten, what fraction was eaten?"
     - **Dimensions**: denominator_max: 8, allowed_denominators: [2,3,4,5,6,8], fraction_type_index: 0.0
     - **Visual Option**: Yes - GridArea (visual fraction model)
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: GridArea
     - **Template Function**: `_gen_grid_area()`
     - **Visual Params**:
       - `shape_type`: "fraction_circle" or "fraction_bar"
       - `denominator`: Number of equal parts (2, 3, 4, 5, 6, or 8)
       - `numerator`: 1 for unit fractions
       - `shaded_parts`: 1
       - `correct_count`: Numerator (1)
     - **Example Output**:
       ```json
       {
         "shape_type": "fraction_circle",
         "denominator": 6,
         "numerator": 1,
         "shaded_parts": 1,
         "correct_count": 1,
         "total_parts": 6,
         "fraction_display": "1/6"
       }
       ```
       *Question: "Shade 1/6 of the circle."*
     - **Question Modes**: interactive (shade parts), mcq (select correct shading), fill_in (type the fraction)

47. **Competency**: Read and write unit fractions in fraction notation.
    - **Generator**: fractions
    - **Example**: "Write 'one fourth' as a fraction."
    - **Status**: Covered

48. **Competency**: Order unit fractions from smallest to largest.
     - **Generator**: fractions
     - **Example**: "Which is larger: 1/3 or 1/5?"
     - **Visual Option**: Yes - SortOrder
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: SortOrder
     - **Template Function**: `_gen_sort_order()`
     - **Visual Params**:
       - `items`: Array of unit fractions (e.g., ["1/2", "1/8", "1/4", "1/3"])
       - `correct_sequence`: Ordered from smallest to largest
       - `direction`: "ascending"
       - `content_type`: "fraction"
       - `same_denominator`: false (unit fractions have numerator 1)
     - **Example Output**:
       ```json
       {
         "items": ["1/2", "1/8", "1/4", "1/3"],
         "correct_sequence": ["1/8", "1/4", "1/3", "1/2"],
         "direction": "ascending",
         "content_type": "fraction",
         "same_denominator": false
       }
       ```
       *Question: "Arrange the fractions from smallest to largest."*
     - **Question Modes**: interactive (drag to order), mcq (select correct order), fill_in (type the sequence)

49. **Competency**: Represent and identify similar fractions with denominators 2, 3, 4, 5, 6, and 8.
     - **Generator**: fractions
     - **Example**: "What fraction is shaded: 3/8?"
     - **Dimensions**: fraction_type_index: 0.3
     - **Visual Option**: Yes - NumberLine
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: NumberLine
     - **Template Function**: `_gen_number_line()`
     - **Visual Params**:
       - `numerator`: Number of parts (e.g., 3)
       - `denominator`: Total parts (2, 3, 4, 5, 6, or 8)
       - `range`: [0, 1]
       - `divisions`: Denominator value
       - `content_type`: "fraction"
       - `correct_position`: Numerator (position on number line)
       - `labels`: ["0", "1"]
     - **Example Output**:
       ```json
       {
         "numerator": 3,
         "denominator": 8,
         "range": [0, 1],
         "divisions": 8,
         "content_type": "fraction",
         "correct_position": 3,
         "labels": ["0", "1"],
         "is_interactive": true
       }
       ```
       *Question: "Move the dot to show 3/8 on the number line."*
     - **Question Modes**: interactive (place marker at fraction), mcq (select marked position), fill_in (type the fraction value)

50. **Competency**: Read and write similar fractions in fraction notation.
    - **Generator**: fractions
    - **Example**: "Write 'three eighths' as a fraction."
    - **Status**: Covered

51. **Competency**: Order similar fractions from smallest to largest.
     - **Generator**: fractions
     - **Example**: "Which is larger: 2/5 or 4/5?"
     - **Dimensions**: like_denominators: 1.0
     - **Visual Option**: Yes - SortOrder
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: SortOrder
     - **Template Function**: `_gen_sort_order()`
     - **Visual Params**:
       - `items`: Array of similar fractions (same denominator)
       - `correct_sequence`: Ordered from smallest to largest
       - `direction`: "ascending"
       - `content_type`: "fraction"
       - `same_denominator`: true
       - `denominator`: Common denominator value
     - **Example Output**:
       ```json
       {
         "items": ["4/5", "1/5", "3/5", "2/5"],
         "correct_sequence": ["1/5", "2/5", "3/5", "4/5"],
         "direction": "ascending",
         "content_type": "fraction",
         "same_denominator": true,
         "denominator": 5
       }
       ```
       *Question: "Arrange the fractions from smallest to largest."*
     - **Question Modes**: interactive (drag to order), mcq (select correct order), fill_in (type the sequence)

### Data and Probability

#### Quarter 3

52. **Competency**: Present raw data, or data in tabular form, in a pictograph with a scale.
     - **Generator**: data_probability
     - **Visual Option**: Yes - BarChart/pictograph (REQUIRED)
     - **Status**: Partial - Visual strongly preferred

     **Visual Skeleton Details**:
     - **Visual Type**: BarChart
     - **Template Function**: `_gen_bar_chart()`
     - **Visual Params**:
       - `labels`: Category names (e.g., ["Apples", "Bananas", "Oranges"])
       - `values`: Data values for each category
       - `values2`: null (single series for pictograph)
       - `series_labels`: null
       - `title`: Chart title
       - `max_y`: Maximum Y-axis value
       - `scale`: Scale factor (e.g., 2 = each symbol = 2 items)
       - `orientation`: "vertical"
       - `is_pictograph`: true
       - `has_scale`: true
       - `is_read_mode`: false (CREATE mode - student builds chart)
       - `is_interactive`: true
     - **Example Output**:
       ```json
       {
         "labels": ["Apples", "Bananas", "Oranges"],
         "values": [8, 6, 10],
         "values2": null,
         "series_labels": null,
         "title": "Fruit Count",
         "max_y": 12,
         "scale": 2,
         "orientation": "vertical",
         "is_pictograph": true,
         "has_scale": true,
         "is_read_mode": false,
         "is_interactive": true
       }
       ```
       *Question: "Make a picture graph. Apples: 8, Bananas: 6, Oranges: 10. Each picture = 2."*
     - **Question Modes**: interactive (create pictograph), fill_in (type values from table)

53. **Competency**: Interpret data in tabular form and in a pictograph with or without scale.
     - **Generator**: data_probability
     - **Example**: "The table shows: Monday: 5 apples, Tuesday: 8 apples. How many total?"
     - **Visual Option**: Yes - BarChart
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: BarChart
     - **Template Function**: `_gen_bar_chart()`
     - **Visual Params**:
       - `labels`: Category names
       - `values`: Pre-filled data values
       - `title`: Chart title
       - `max_y`: Y-axis maximum
       - `scale`: 1 or 2 (for pictographs with scale)
       - `is_pictograph`: Boolean
       - `has_scale`: Boolean
       - `is_read_mode`: true (READ mode - chart is pre-filled)
       - `is_interactive`: false
       - `ask_category`: Specific category to ask about (optional)
     - **Example Output**:
       ```json
       {
         "labels": ["Monday", "Tuesday", "Wednesday"],
         "values": [5, 8, 6],
         "title": "Apples Sold",
         "max_y": 10,
         "scale": 1,
         "is_pictograph": true,
         "has_scale": false,
         "is_read_mode": true,
         "is_interactive": false,
         "ask_category": "Tuesday"
       }
       ```
       *Question: "Look at the picture graph. How many apples on Tuesday?"*
     - **Question Modes**: mcq (select value), fill_in (type the value), read_bar (read chart)


---

## Grade 3

### Measurement and Geometry

#### Quarter 1

54. **Competency**: Illustrate and estimate the area of a square or rectangle using square tile units.
     - **Generator**: measurement
     - **Example**: "A rectangle is 5 units long and 3 units wide. What is its area?"
     - **Dimensions**: measurement_type: "length", computation_required: 0.6
     - **Visual Option**: Yes - GridArea visual
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: GridArea
     - **Template Function**: `_gen_grid_area()`
     - **Visual Params**:
       - `grid_size`: [10, 10] - Grid dimensions
       - `shape_type`: "rectangle"
       - `width`: Width in grid units (e.g., 5)
       - `height`: Height in grid units (e.g., 3)
       - `correct_count`: Area (width × height)
       - `measure_type`: "area"
     - **Example Output**:
       ```json
       {
         "grid_size": [10, 10],
         "shape_type": "rectangle",
         "width": 5,
         "height": 3,
         "correct_count": 15,
         "measure_type": "area"
       }
       ```
       *Question: "Shade all the squares inside the 5×3 rectangle. How many square units is the area?"*
     - **Question Modes**: interactive (shade grid squares), mcq (select area), fill_in (type the area)

55. **Competency**: Explore inductively the derivation of the formulas for the areas of a square and a rectangle.
     - **Generator**: measurement (conceptual)
     - **Dimensions**: abstraction_level: 0.7
     - **Visual Option**: Yes - GridArea
     - **Status**: Partial

     **Visual Skeleton Details**:
     - **Visual Type**: GridArea
     - **Template Function**: `_gen_grid_area()`
     - **Visual Params**:
       - `grid_size`: [10, 10]
       - `shape_type`: "rectangle" or "square"
       - `width`: Variable width
       - `height`: Variable height
       - `correct_count`: Area (w × h)
       - `show_multiple_examples`: true - Show several rectangles
       - `discover_formula`: true - Guide to discover length × width
     - **Example Output**:
       ```json
       {
         "grid_size": [10, 10],
         "shape_type": "rectangle",
         "examples": [
           {"width": 2, "height": 3, "area": 6},
           {"width": 4, "height": 2, "area": 8},
           {"width": 3, "height": 5, "area": 15}
         ],
         "correct_count": null,
         "discover_formula": true,
         "prompt": "What pattern do you see?"
       }
       ```
     - **Question Modes**: interactive (explore multiple rectangles), fill_in (discover the formula)

56. **Competency**: Find the areas of squares and rectangles in sq. cm and sq. m.
     - **Generator**: measurement
     - **Example**: "Find the area of a square with sides of 6 cm."
     - **Dimensions**: value_max: 100, unit_familiarity: 0.5
     - **Visual Option**: Yes - GridArea
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: GridArea
     - **Template Function**: `_gen_grid_area()`
     - **Visual Params**:
       - `grid_size`: [10, 10]
       - `shape_type`: "rectangle" or "square"
       - `width`: Width with unit (cm or m)
       - `height`: Height with unit
       - `unit`: "sq. cm" or "sq. m"
       - `correct_count`: Area value
     - **Example Output**:
       ```json
       {
         "grid_size": [10, 10],
         "shape_type": "square",
         "width": 6,
         "height": 6,
         "unit": "sq. cm",
         "correct_count": 36,
         "labels": ["6 cm", "6 cm"]
       }
       ```
       *Question: "Find the area of this square with sides of 6 cm."*
     - **Question Modes**: interactive (count squares), mcq (select area), fill_in (type area with units)

57. **Competency**: Solve problems involving areas of squares and rectangles.
     - **Generator**: measurement
     - **Example**: "A room is 8m by 5m. How many square meters of carpet are needed?"
     - **Dimensions**: step_count: 1-2, context_complexity: 0.5
     - **Visual Option**: Yes - GridArea
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: GridArea
     - **Template Function**: `_gen_grid_area()`
     - **Visual Params**:
       - `grid_size`: [10, 10]
       - `shape_type`: "rectangle"
       - `width`: Width (e.g., 8)
       - `height`: Height (e.g., 5)
       - `unit`: "sq. m"
       - `context`: Problem context (e.g., "room", "garden")
       - `correct_count`: Area
     - **Example Output**:
       ```json
       {
         "grid_size": [10, 10],
         "shape_type": "rectangle",
         "width": 8,
         "height": 5,
         "unit": "sq. m",
         "context": "room",
         "correct_count": 40,
         "labels": ["8 m", "5 m"]
       }
       ```
       *Question: "A room is 8m by 5m. How many square meters of carpet are needed?"*
     - **Question Modes**: interactive (visualize and calculate), mcq (select area), fill_in (type answer with units)

58. **Competency**: Recognize, using models, and draws a point, line, line segment, and ray.
    - **Generator**: geometry_props
    - **Example**: "Which shows a ray: A→ or •A or A—B ?"
    - **Dimensions**: shape_complexity: 0.2, abstraction_level: 0.5
    - **Visual Option**: Yes
    - **Status**: Partial

59. **Competency**: Recognize and draw parallel, intersecting, and perpendicular lines.
    - **Generator**: geometry_props
    - **Dimensions**: shape_complexity: 0.3, property_type: 0.5
    - **Visual Option**: Yes
    - **Status**: Partial

60. **Competency**: Identify and draw line segments of equal length using a ruler.
    - **Generator**: geometry_props
    - **Dimensions**: value_max: 20
    - **Visual Option**: Yes
    - **Status**: Partial

#### Quarter 2

61. **Competency**: Measure mass in grams (g), kilograms (kg) and/or milligrams (mg).
    - **Generator**: measurement
    - **Dimensions**: measurement_type: "mass", value_max: 1000
    - **Visual Option**: No
    - **Status**: Partial

62. **Competency**: Estimate mass of an object using grams, kilograms, and/or milligrams.
    - **Generator**: measurement
    - **Dimensions**: abstraction_level: 0.7
    - **Visual Option**: No
    - **Status**: Partial

63. **Competency**: Compare masses of objects including the use of a balance scale.
     - **Generator**: measurement
     - **Dimensions**: measurement_type: "mass"
     - **Visual Option**: Yes - Categorize (balance scale simulation)
     - **Status**: Partial

     **Visual Skeleton Details**:
     - **Visual Type**: Categorize (adapted for comparison)
     - **Template Function**: `_gen_categorize()`
     - **Visual Params**:
       - `comparison_type`: "mass_balance"
       - `objects`: List of objects with masses
       - `categories`: ["Heavier", "Lighter", "Equal"]
       - `comparisons`: Pairs of objects to compare
       - `correct_categories`: Which is heavier for each pair
     - **Example Output**:
       ```json
       {
         "comparison_type": "mass_balance",
         "objects": ["Apple", "Book", "Pencil", "Eraser"],
         "categories": ["Heavier", "Lighter"],
         "comparisons": [
           {"left": "Book", "right": "Apple"},
           {"left": "Pencil", "right": "Eraser"}
         ],
         "correct_categories": {
           "Book_vs_Apple": "Heavier",
           "Pencil_vs_Eraser": "Heavier"
         }
       }
       ```
     - **Question Modes**: interactive (drag to balance scale), mcq (select heavier/lighter), fill_in (type comparison result)

64. **Competency**: Measure capacity in liters (L) and/or milliliters (mL).
    - **Generator**: measurement
    - **Example**: "How many milliliters are in 2 liters?"
    - **Dimensions**: measurement_type: "capacity", conversion_steps: 1
    - **Visual Option**: No
    - **Status**: Partial

65. **Competency**: Estimate capacity using liters and/or milliliters.
    - **Generator**: measurement
    - **Dimensions**: abstraction_level: 0.7
    - **Visual Option**: No
    - **Status**: Partial

66. **Competency**: Compare capacities of two containers.
     - **Generator**: measurement
     - **Dimensions**: measurement_type: "capacity"
     - **Visual Option**: Yes - Categorize
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: Categorize
     - **Template Function**: `_gen_categorize()`
     - **Visual Params**:
       - `comparison_type`: "capacity"
       - `containers`: List of containers with capacities
       - `categories`: ["Holds More", "Holds Less", "Same"]
       - `correct_categories`: Comparison results
     - **Example Output**:
       ```json
       {
         "comparison_type": "capacity",
         "containers": ["Jug A (2L)", "Jug B (1.5L)", "Bottle (500mL)"],
         "categories": ["Holds Most", "Holds Least"],
         "correct_categories": {
           "Jug A": "Holds Most",
           "Bottle": "Holds Least"
         }
       }
       ```
     - **Question Modes**: interactive (compare containers), mcq (select which holds more), fill_in (type capacity comparison)

#### Quarter 4

67. **Competency**: Describe and draw the effect of a two-direction multi-step slide (or translation).
     - **Generator**: geometry_props
     - **Dimensions**: shape_complexity: 0.3, property_type: 0.6
     - **Visual Option**: Yes - GridArea
     - **Status**: Partial

     **Visual Skeleton Details**:
     - **Visual Type**: GridArea
     - **Template Function**: `_gen_grid_area()`
     - **Visual Params**:
       - `grid_size`: [10, 10]
       - `shape_type`: "translatable_shape"
       - `initial_position`: [x, y]
       - `translation`: [dx, dy] - Two-direction translation
       - `correct_count`: Final position [x+dx, y+dy]
       - `steps`: 2 (slide right then up, etc.)
     - **Example Output**:
       ```json
       {
         "grid_size": [10, 10],
         "shape_type": "translatable_shape",
         "initial_position": [2, 3],
         "translation": [4, 2],
         "correct_count": [6, 5],
         "steps": 2,
         "step_description": "Slide 4 right, then 2 up"
       }
       ```
     - **Question Modes**: interactive (perform translation), mcq (select final position), fill_in (type final coordinates)

68. **Competency**: Identify shapes or figures that show line symmetry by drawing the line of symmetry.
     - **Generator**: geometry_props
     - **Dimensions**: shape_complexity: 0.3, property_type: 0.6
     - **Visual Option**: Yes - Categorize or GridArea
     - **Status**: Partial

     **Visual Skeleton Details**:
     - **Visual Type**: Categorize (for sorting symmetric/asymmetric) or GridArea (for drawing lines)
     - **Template Function**: `_gen_categorize()` or `_gen_grid_area()`
     - **Visual Params**:
       - `task_type`: "identify_symmetry"
       - `shapes`: List of shape names/images
       - `categories`: ["Has Line Symmetry", "No Line Symmetry"]
       - `correct_categories`: Mapping of shapes to categories
       - `symmetry_lines`: For symmetric shapes, where the line is
     - **Example Output**:
       ```json
       {
         "task_type": "identify_symmetry",
         "shapes": ["Square", "Rectangle", "Triangle", "Circle", "Scalene Triangle"],
         "categories": ["Has Line Symmetry", "No Line Symmetry"],
         "correct_categories": {
           "Square": "Has Line Symmetry",
           "Rectangle": "Has Line Symmetry",
           "Triangle": "Has Line Symmetry",
           "Circle": "Has Line Symmetry",
           "Scalene Triangle": "No Line Symmetry"
         },
         "symmetry_lines": {
           "Square": ["vertical", "horizontal", "diagonal"]
         }
       }
       ```
     - **Question Modes**: interactive (sort shapes or draw symmetry lines), mcq (select symmetric shapes), fill_in (describe symmetry)

69. **Competency**: Complete a figure that is symmetric with respect to a line.
     - **Generator**: geometry_props
     - **Dimensions**: property_type: 0.7
     - **Visual Option**: Yes - GridArea (REQUIRED)
     - **Status**: Partial

     **Visual Skeleton Details**:
     - **Visual Type**: GridArea
     - **Template Function**: `_gen_grid_area()`
     - **Visual Params**:
       - `grid_size`: [10, 10]
       - `shape_type`: "symmetry_completion"
       - `symmetry_line`: "vertical", "horizontal", or "diagonal"
       - `given_half`: Coordinates of given half
       - `correct_count`: Number of squares to complete
       - `completion_coords`: Coordinates for the mirrored half
     - **Example Output**:
       ```json
       {
         "grid_size": [10, 10],
         "shape_type": "symmetry_completion",
         "symmetry_line": "vertical",
         "symmetry_line_x": 5,
         "given_half": [[4, 3], [4, 4], [4, 5], [3, 4]],
         "correct_count": 4,
         "completion_coords": [[6, 3], [6, 4], [6, 5], [7, 4]]
       }
       ```
       *Question: "Complete this shape so it has line symmetry."*
     - **Question Modes**: interactive (shade squares to complete), mcq (select completion), fill_in (describe coordinates)

### Number and Algebra

#### Quarter 1

70. **Competency**: Represent numbers up to 10 000 using pictorial models and numerals.
     - **Generator**: place_value
     - **Example**: "In 7,432, what digit is in the hundreds place?"
     - **Dimensions**: digit_count: 4, target_place: 0-3
     - **Visual Option**: Yes - FillInTable
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: FillInTable
     - **Template Function**: `_gen_fill_in_table()`
     - **Visual Params**:
       - `columns`: ["Number", "Thousands", "Hundreds", "Tens", "Ones"]
       - `rows`: 4-digit numbers with blanks
       - `blank_inputs`: Cell positions to fill
       - `correct_fills`: Correct digit values
       - `pattern_type`: "place_value"
     - **Example Output**:
       ```json
       {
         "columns": ["Number", "Thousands", "Hundreds", "Tens", "Ones"],
         "rows": [
           [7432, 7, null, 3, 2],
           [5891, null, 8, 9, 1],
           [6204, 6, 2, null, 4]
         ],
         "blank_inputs": [2, 3, 4],
         "correct_fills": [4, 5, 0],
         "pattern_type": "place_value"
       }
       ```
     - **Question Modes**: interactive (fill in blanks), mcq (select correct digit), fill_in (type the digit)

71. **Competency**: Read and write numbers up to 10 000 in numerals and in words.
    - **Generator**: place_value
    - **Dimensions**: digit_count: 4
    - **Visual Option**: No
    - **Status**: Partial

72. **Competency**: Describe the position of objects using ordinal numbers up to 100th.
    - **Generator**: counting
    - **Dimensions**: ordinal_max: 100
    - **Visual Option**: No
    - **Status**: Covered

73. **Competency**: Determine the place value of a digit in a 4-digit number, the value of a digit, and the digit of number.
     - **Generator**: place_value
     - **Example**: "In 8,765, what is the VALUE of the digit 8?"
     - **Dimensions**: digit_count: 4, target_place: 0-3
     - **Visual Option**: Yes - FillInTable
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: FillInTable
     - **Template Function**: `_gen_fill_in_table()`
     - **Visual Params**:
       - `columns`: ["Digit", "Place Value", "Value"]
       - `rows`: One row per digit in the number
       - `blank_inputs`: Which values to fill
       - `correct_fills`: Correct answers
       - `number`: The 4-digit number being analyzed
     - **Example Output**:
       ```json
       {
         "number": 8765,
         "columns": ["Digit", "Place Value", "Value"],
         "rows": [
           [8, "Thousands", null],
           [7, null, 700],
           [6, "Tens", null],
           [5, null, 5]
         ],
         "blank_inputs": [1, 2, 3],
         "correct_fills": [8000, "Hundreds", 50],
         "pattern_type": "place_value_analysis"
       }
       ```
     - **Question Modes**: interactive (complete table), mcq (select values), fill_in (type answers)

74. **Competency**: Round numbers to the nearest ten, hundred, or thousand.
     - **Generator**: place_value
     - **Example**: "Round 4,567 to the nearest hundred."
     - **Visual Option**: Yes - NumberLine
     - **Status**: Partial

     **Visual Skeleton Details**:
     - **Visual Type**: NumberLine
     - **Template Function**: `_gen_number_line()`
     - **Visual Params**:
       - `value`: Number to round (4567)
       - `round_to`: "ten", "hundred", or "thousand"
       - `range`: Appropriate bounds around the number
       - `divisions`: Scale based on round_to
       - `content_type`: "rounding"
       - `correct_position`: Rounded value position
       - `marker_positions`: Key positions (lower, upper, midpoint)
     - **Example Output**:
       ```json
       {
         "value": 4567,
         "round_to": "hundred",
         "range": [4500, 4600],
         "divisions": 10,
         "content_type": "rounding",
         "correct_position": 4600,
         "marker_positions": [4567, 4550, 4600],
         "labels": ["4500", "4600"],
         "is_interactive": true
       }
       ```
       *Question: "Round 4,567 to the nearest hundred. Mark the answer on the number line."*
     - **Question Modes**: interactive (mark rounded value), mcq (select correct rounding), fill_in (type rounded number)

75. **Competency**: Compare numbers up to 10 000 using the symbols =, >, and <.
     - **Generator**: compare_order
     - **Example**: "Which symbol: 5,432 ___ 5,342?"
     - **Dimensions**: max_number: 10000
     - **Visual Option**: Yes - SortOrder or NumberLine
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: NumberLine (for comparing two numbers)
     - **Template Function**: `_gen_number_line()`
     - **Visual Params**:
       - `value1`: First number (5432)
       - `value2`: Second number (5342)
       - `range`: [0, 10000] or scaled range
       - `divisions`: Appropriate scale
       - `content_type`: "comparison"
       - `correct_position`: Position of larger number or both marked
       - `comparison_result`: ">", "<", or "="
     - **Example Output**:
       ```json
       {
         "value1": 5432,
         "value2": 5342,
         "range": [5300, 5500],
         "divisions": 20,
         "content_type": "comparison",
         "comparison_result": ">",
         "correct_position": null,
         "show_both": true,
         "labels": ["5300", "5500"],
         "is_interactive": false
       }
       ```
       *Question: "Compare: 5,432 ___ 5,342. Use >, <, or =."*
     - **Question Modes**: mcq (select symbol), fill_in (type the symbol)

76. **Competency**: Order numbers up to 10 000 from smallest to largest.
     - **Generator**: compare_order
     - **Visual Option**: Yes - SortOrder (RECOMMENDED)
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: SortOrder
     - **Template Function**: `_gen_sort_order()`
     - **Visual Params**:
       - `items`: Array of 4-digit numbers (3-5 numbers)
       - `correct_sequence`: Sorted from smallest to largest
       - `direction`: "ascending"
       - `content_type`: "whole"
       - `max_value`: 10000
     - **Example Output**:
       ```json
       {
         "items": [5432, 1890, 7205, 3456, 9012],
         "correct_sequence": [1890, 3456, 5432, 7205, 9012],
         "direction": "ascending",
         "content_type": "whole",
         "max_value": 10000
       }
       ```
       *Question: "Arrange the numbers from smallest to largest."*
     - **Question Modes**: interactive (drag to order), mcq (select correct order), fill_in (type the sequence)

#### Quarter 2

77. **Competency**: Read and write money in words and using Philippine currency symbols up to 10 000.
     - **Generator**: arithmetic (money)
     - **Dimensions**: operand_max: 10000
     - **Visual Option**: Yes - PesoMoney
     - **Status**: Partial

     **Visual Skeleton Details**:
     - **Visual Type**: PesoMoney
     - **Template Function**: `_gen_peso_money()`
     - **Visual Params**:
       - `target_amount`: Amount to represent (e.g., 8450)
       - `representation_mode`: "symbolic" or "words"
       - `available_denominations`: [1, 5, 10, 20, 50, 100, 200, 500, 1000]
       - `show_in_words`: true - Show word representation
       - `show_symbolic`: true - Show ₱ symbol
     - **Example Output**:
       ```json
       {
         "target_amount": 8450,
         "representation_mode": "both",
         "available_denominations": [1, 5, 10, 20, 50, 100, 200, 500, 1000],
         "amount_in_words": "Eight thousand four hundred fifty pesos",
         "amount_symbolic": "₱8,450.00",
         "show_in_words": true,
         "show_symbolic": true
       }
       ```
       *Question: "Write ₱8,450 in words." or "Read 'Eight thousand four hundred fifty pesos' and show it."*
     - **Question Modes**: interactive (show amount with bills/coins), mcq (match word to amount), fill_in (write amount in words)

78. **Competency**: Add numbers with sums up to 10 000, with and without regrouping.
    - **Generator**: arithmetic
    - **Example**: "3,456 + 2,847 = ?"
    - **Dimensions**: operand_max: 10000
    - **Status**: Covered

79. **Competency**: Estimate the sum of addends with up to 4 digits.
    - **Generator**: arithmetic
    - **Dimensions**: abstraction_level: 0.7
    - **Status**: Partial

80. **Competency**: Solve problems involving addition of numbers with sums up to 10 000, including money.
     - **Generator**: arithmetic
     - **Example**: "A laptop costs 8,500 and a bag costs 1,250. Total cost?"
     - **Visual Option**: Yes - PesoMoney
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: PesoMoney
     - **Template Function**: `_gen_peso_money()`
     - **Visual Params**:
       - `problem_type`: "addition"
       - `item1_amount`: First amount (8500)
       - `item2_amount`: Second amount (1250)
       - `target_amount`: Sum (9750)
       - `context`: Problem context
     - **Example Output**:
       ```json
       {
         "problem_type": "addition",
         "item1_amount": 8500,
         "item2_amount": 1250,
         "target_amount": 9750,
         "context": "A laptop costs ₱8,500 and a bag costs ₱1,250.",
         "available_denominations": [1, 5, 10, 20, 50, 100, 200, 500, 1000],
         "show_items": true
       }
       ```
       *Question: "A laptop costs ₱8,500 and a bag costs ₱1,250. What is the total cost?"*
     - **Question Modes**: interactive (show total amount), mcq (select total), fill_in (type the sum)

81. **Competency**: Subtract numbers, where both numbers are less than 10 000, with and without regrouping.
    - **Generator**: arithmetic
    - **Example**: "7,234 - 3,567 = ?"
    - **Dimensions**: operand_max: 10000
    - **Status**: Covered

82. **Competency**: Estimate the difference of two numbers of up to 4 digits.
    - **Generator**: arithmetic
    - **Dimensions**: abstraction_level: 0.7
    - **Status**: Partial

83. **Competency**: Perform addition and subtraction of 3 to 4 numbers of up to 2 digits.
    - **Generator**: arithmetic
    - **Example**: "25 + 38 - 17 + 42 = ?"
    - **Dimensions**: step_count: 3-4
    - **Status**: Covered

84. **Competency**: Solve problems involving addition and subtraction with 3 to 4 numbers, including money.
     - **Generator**: arithmetic
     - **Dimensions**: step_count: 3-4, context_complexity: 0.6
     - **Visual Option**: Yes - PesoMoney
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: PesoMoney
     - **Template Function**: `_gen_peso_money()`
     - **Visual Params**:
       - `problem_type`: "multi_step"
       - `operations`: Sequence of + and - operations
       - `amounts`: List of amounts
       - `target_amount`: Final result
       - `step_count`: 3-4 steps
     - **Example Output**:
       ```json
       {
         "problem_type": "multi_step",
         "operations": ["+", "-", "+"],
         "amounts": [2500, 1800, 900, 1200],
         "target_amount": 4600,
         "step_count": 4,
         "available_denominations": [1, 5, 10, 20, 50, 100, 200, 500, 1000],
         "context": "Shopping with multiple items and change"
       }
       ```
       *Question: "You have ₱2,500. You earn ₱1,800, spend ₱900, then receive ₱1,200. How much do you have?"*
     - **Question Modes**: interactive (track amount through steps), mcq (select final amount), fill_in (type final amount)

#### Quarter 3

85. **Competency**: Multiply numbers using the 6, 7, 8, and 9 multiplication tables.
    - **Generator**: arithmetic
    - **Example**: "8 x 7 = ?"
    - **Dimensions**: divisibility_difficulty: 0.3
    - **Status**: Covered

86. **Competency**: Illustrate and apply properties of multiplication for the 6, 7, 8, and 9 tables.
    - **Generator**: arithmetic
    - **Dimensions**: abstraction_level: 0.6
    - **Status**: Partial

87. **Competency**: Multiply numbers with and without regrouping: 2- to 3-digit by 1-digit, products up to 10 000.
    - **Generator**: arithmetic
    - **Example**: "347 x 6 = ?"
    - **Dimensions**: operand_max: 10000, operand_digit_count: 2-4
    - **Status**: Covered

88. **Competency**: Estimate the product of 2- to 3-digit numbers by 1- to 2-digit numbers.
    - **Generator**: arithmetic
    - **Dimensions**: abstraction_level: 0.7
    - **Status**: Partial

89. **Competency**: Solve 1-to 2-step multiplication problems, including money.
     - **Generator**: arithmetic
     - **Example**: "If one shirt costs 250, how much do 8 shirts cost?"
     - **Visual Option**: Yes - PesoMoney
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: PesoMoney
     - **Template Function**: `_gen_peso_money()`
     - **Visual Params**:
       - `problem_type`: "multiplication"
       - `unit_price`: Price per item (250)
       - `quantity`: Number of items (8)
       - `target_amount`: Total cost (2000)
       - `context`: Shopping scenario
     - **Example Output**:
       ```json
       {
         "problem_type": "multiplication",
         "unit_price": 250,
         "quantity": 8,
         "target_amount": 2000,
         "context": "If one shirt costs ₱250, how much do 8 shirts cost?",
         "available_denominations": [1, 5, 10, 20, 50, 100, 200, 500],
         "show_quantity": true
       }
       ```
     - **Question Modes**: interactive (make total amount), mcq (select total), fill_in (type the cost)

90. **Competency**: Determine the missing term/s in a pattern with repeating and increasing components.
     - **Generator**: counting
     - **Example**: "What comes next? 2a, 2b, 2c, 3a, ___"
     - **Dimensions**: direction_complexity: 0.5
     - **Visual Option**: Yes - RuleDiscovery
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: RuleDiscovery
     - **Template Function**: `_gen_rule_discovery()`
     - **Visual Params**:
       - `table`: Pattern terms with position numbers
       - `rule_expression`: Pattern rule (e.g., "number increases, letter cycles")
       - `variable_name`: "n"
       - `pattern_type`: "compound" (both number and letter pattern)
       - `missing_terms`: Positions to fill
     - **Example Output**:
       ```json
       {
         "table": [[1, "2a"], [2, "2b"], [3, "2c"], [4, "3a"], [5, null]],
         "rule_expression": "number=floor((n+2)/3)+1, letter=chr(ord('a')+(n-1)%3)",
         "variable_name": "n",
         "pattern_type": "compound",
         "missing_terms": [5],
         "correct_fills": ["3b"]
       }
       ```
       *Question: "What comes next? 2a, 2b, 2c, 3a, ___"*
     - **Question Modes**: interactive (complete pattern), mcq (select next term), fill_in (type the missing term)

91. **Competency**: Explain how to generate a given pattern with repeating and increasing components.
     - **Generator**: counting
     - **Dimensions**: abstraction_level: 0.7
     - **Visual Option**: Yes - RuleDiscovery
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: RuleDiscovery
     - **Template Function**: `_gen_rule_discovery()`
     - **Visual Params**:
       - `table`: Complete pattern table
       - `rule_expression`: The rule (e.g., "n*2+1")
       - `variable_name`: "n"
       - `pattern_type`: "linear" or "compound"
       - `explain_mode`: true - Student describes the rule
     - **Example Output**:
       ```json
       {
         "table": [[1, 3], [2, 5], [3, 7], [4, 9], [5, 11]],
         "rule_expression": "2*n+1",
         "variable_name": "n",
         "pattern_type": "linear",
         "explain_mode": true,
         "prompt": "Explain how to get each output from its input number."
       }
       ```
       *Question: "Explain the rule for this pattern: 3, 5, 7, 9, 11..."*
     - **Question Modes**: fill_in (write rule explanation), interactive (describe steps)

#### Quarter 4

92. **Competency**: Illustrate division through equal jumps on the number line and as inverse of multiplication.
     - **Generator**: arithmetic
     - **Example**: "48 / 6 = ? (Think: 6 x ? = 48)"
     - **Visual Option**: Yes - NumberLine
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: NumberLine
     - **Template Function**: `_gen_number_line()`
     - **Visual Params**:
       - `dividend`: Total distance (48)
       - `divisor`: Jump size (6)
       - `range`: [0, dividend]
       - `content_type`: "division_jumps"
       - `correct_position`: Number of jumps (quotient)
       - `show_jumps`: true
       - `jump_direction`: "forward"
       - `jump_size`: Divisor value
     - **Example Output**:
       ```json
       {
         "dividend": 48,
         "divisor": 6,
         "range": [0, 48],
         "divisions": 48,
         "content_type": "division_jumps",
         "correct_position": 8,
         "show_jumps": true,
         "jump_direction": "forward",
         "jump_size": 6,
         "inverse_multiplication": "6 × 8 = 48",
         "labels": ["0", "48"],
         "is_interactive": true
       }
       ```
       *Question: "Show 48 ÷ 6 by making jumps of 6 on the number line. How many jumps?"*
     - **Question Modes**: interactive (make equal jumps), mcq (select quotient), fill_in (type number of jumps)

93. **Competency**: Divide numbers using the 6, 7, 8, and 9 multiplication tables.
    - **Generator**: arithmetic
    - **Example**: "63 / 7 = ?"
    - **Dimensions**: divisibility_difficulty: 0.3
    - **Status**: Covered

94. **Competency**: Find the missing number in a number sentence involving multiplication or division by 6, 7, 8, and 9.
    - **Generator**: arithmetic
    - **Example**: "___ x 8 = 64"
    - **Status**: Covered

95. **Competency**: Divide numbers with and without remainder: 2- to 3-digit by 1-digit.
    - **Generator**: arithmetic
    - **Example**: "157 / 6 = ?" (with remainder) or "450 / 10 = ?"
    - **Dimensions**: operand_max: 10000, include_remainder: 0.0-1.0
    - **Status**: Covered

96. **Competency**: Estimate the quotient of 2- to 3-digit numbers divided by 1- to 2-digit numbers.
    - **Generator**: arithmetic
    - **Dimensions**: abstraction_level: 0.7
    - **Status**: Partial

97. **Competency**: Solve division problems involving 2- to 3-digit numbers by a 1-digit number, including money.
     - **Generator**: arithmetic
     - **Example**: "450 is shared equally among 6 people."
     - **Visual Option**: Yes - PesoMoney
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: PesoMoney
     - **Template Function**: `_gen_peso_money()`
     - **Visual Params**:
       - `problem_type`: "division"
       - `total_amount`: Amount to divide (450)
       - `divisor`: Number of people (6)
       - `target_amount`: Each person's share (75)
       - `context`: Sharing scenario
     - **Example Output**:
       ```json
       {
         "problem_type": "division",
         "total_amount": 450,
         "divisor": 6,
         "target_amount": 75,
         "context": "₱450 is shared equally among 6 people.",
         "available_denominations": [1, 5, 10, 20, 50, 100, 200],
         "show_sharing": true
       }
       ```
       *Question: "₱450 is shared equally among 6 people. How much does each person get?"*
     - **Question Modes**: interactive (distribute equally), mcq (select share amount), fill_in (type quotient)

98. **Competency**: Represent fractions that are equal to one and greater than one using models.
     - **Generator**: fractions
     - **Example**: "How many fourths make one whole?"
     - **Dimensions**: fraction_type_index: 0.6-1.0
     - **Visual Option**: Yes - NumberLine or GridArea
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: NumberLine (for improper/mixed) or GridArea (for visual models)
     - **Template Function**: `_gen_number_line()` or `_gen_grid_area()`
     - **Visual Params** (NumberLine for improper/mixed):
       - `numerator`: Numerator (e.g., 5 for 5/4)
       - `denominator`: Denominator (4)
       - `content_type`: "improper_fraction" or "mixed_number"
       - `range`: [0, 2] or [0, 3]
       - `correct_position`: Position on number line
       - `fraction_display`: "5/4" or "1 1/4"
     - **Example Output**:
       ```json
       {
         "numerator": 5,
         "denominator": 4,
         "content_type": "improper_fraction",
         "range": [0, 2],
         "divisions": 8,
         "correct_position": 5,
         "fraction_display": "5/4",
         "mixed_form": "1 1/4",
         "labels": ["0", "2"],
         "is_interactive": true
       }
       ```
       *Question: "Show 5/4 (or 1 1/4) on the number line."*
     - **Question Modes**: interactive (place marker), mcq (select position), fill_in (type the value)

99. **Competency**: Add and subtract similar fractions using models.
     - **Generator**: fractions
     - **Example**: "2/5 + 1/5 = ?"
     - **Dimensions**: like_denominators: 1.0, operation_complexity: 0.5
     - **Visual Option**: Yes - NumberLine
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: NumberLine
     - **Template Function**: `_gen_number_line()`
     - **Visual Params**:
       - `operation`: "add" or "subtract"
       - `fraction1`: First fraction (2/5)
       - `fraction2`: Second fraction (1/5)
       - `denominator`: Common denominator (5)
       - `content_type`: "fraction_operation"
       - `range`: [0, 1] or appropriate
       - `correct_position`: Result position (3/5)
       - `show_jumps`: true
     - **Example Output**:
       ```json
       {
         "operation": "add",
         "fraction1": "2/5",
         "fraction2": "1/5",
         "denominator": 5,
         "content_type": "fraction_operation",
         "range": [0, 1],
         "divisions": 5,
         "correct_position": 3,
         "result_fraction": "3/5",
         "show_jumps": true,
         "labels": ["0", "1"],
         "is_interactive": true
       }
       ```
       *Question: "Show 2/5 + 1/5 on the number line."*
     - **Question Modes**: interactive (make jumps), mcq (select result), fill_in (type the sum/difference)

### Data and Probability

#### Quarter 3

100. **Competency**: Collect data from experiments with a small number of possible outcomes.
     - **Generator**: data_probability
     - **Dimensions**: probability_complexity: 0.0
     - **Visual Option**: No
     - **Status**: Partial

101. **Competency**: Present data in tables and single bar graphs (horizontal and vertical).
     - **Generator**: data_probability
     - **Visual Option**: Yes - BarChart (REQUIRED)
     - **Status**: Partial

     **Visual Skeleton Details**:
     - **Visual Type**: BarChart
     - **Template Function**: `_gen_bar_chart()`
     - **Visual Params**:
       - `labels`: Category names
       - `values`: Data values
       - `values2`: null (single bar chart)
       - `orientation`: "vertical" or "horizontal"
       - `is_pictograph`: false
       - `is_read_mode`: false (CREATE mode)
       - `is_interactive`: true
       - `max_y`: Y-axis maximum
       - `scale`: 1 (unit scale)
     - **Example Output**:
       ```json
       {
         "labels": ["Math", "Science", "English", "Filipino"],
         "values": [25, 30, 20, 28],
         "values2": null,
         "orientation": "vertical",
         "is_pictograph": false,
         "is_read_mode": false,
         "is_interactive": true,
         "title": "Subject Scores",
         "max_y": 35,
         "scale": 1
       }
       ```
       *Question: "Create a bar graph. Math: 25, Science: 30, English: 20, Filipino: 28."*
     - **Question Modes**: interactive (build bar graph), fill_in (enter values)

102. **Competency**: Interpret data in tables and single bar graphs (horizontal and vertical).
     - **Generator**: data_probability
     - **Visual Option**: Yes - BarChart
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: BarChart
     - **Template Function**: `_gen_bar_chart()`
     - **Visual Params**:
       - `labels`: Category names
       - `values`: Pre-filled data values
       - `orientation`: "vertical" or "horizontal"
       - `is_read_mode`: true (READ mode - chart pre-filled)
       - `is_interactive`: false
       - `ask_category`: Specific category to ask about (optional)
     - **Example Output**:
       ```json
       {
         "labels": ["Math", "Science", "English", "Filipino"],
         "values": [25, 30, 20, 28],
         "orientation": "vertical",
         "is_read_mode": true,
         "is_interactive": false,
         "title": "Subject Scores",
         "max_y": 35,
         "ask_category": "Science"
       }
       ```
       *Question: "Look at the bar graph. What is the score for Science?"*
     - **Question Modes**: mcq (select value), fill_in (type the value), read_bar

103. **Competency**: Solve problems using data presented in a single bar graph.
     - **Generator**: data_probability
     - **Dimensions**: step_count: 1-2
     - **Visual Option**: Yes - BarChart
     - **Status**: Covered

     **Visual Skeleton Details**:
     - **Visual Type**: BarChart
     - **Template Function**: `_gen_bar_chart()`
     - **Visual Params**:
       - `labels`: Category names
       - `values`: Pre-filled data values
       - `is_read_mode`: true
       - `problem_type`: "comparison", "total", or "difference"
       - `ask_categories`: Which categories to compare
       - `operation`: "add", "subtract", or "compare"
     - **Example Output**:
       ```json
       {
         "labels": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
         "values": [15, 22, 18, 25, 20],
         "is_read_mode": true,
         "problem_type": "comparison",
         "ask_categories": ["Tuesday", "Thursday"],
         "operation": "compare",
         "correct_answer": "Thursday",
         "difference": 3
       }
       ```
       *Question: "Which day had more sales: Tuesday or Thursday? By how much?"*
     - **Question Modes**: mcq (select answer), fill_in (type answer with calculation)

104. **Competency**: Describe and compare outcomes using: equally likely, less/least likely, more/most likely, certain, impossible.
     - **Generator**: data_probability
     - **Dimensions**: probability_complexity: 0.3-0.5
     - **Status**: Covered

---

## Generator Reference

| Generator Type | Code | Description | Grades | Key Dimensions |
|----------------|------|-------------|--------|----------------|
| counting | cnt | Counting, skip counting, ordinals | 1-3 | max_number, skip_interval, ordinal_max, direction_complexity |
| place_value | pv | Place value, expanded form, digit values | 1-6 | digit_count, target_place, include_zeros, question_type |
| arithmetic | ar | Add, subtract, multiply, divide | 1-6 | operand_max, regrouping_probability, step_count, include_remainder |
| fractions | fr | Fraction identification, comparison, operations | 1-6 | denominator_max, allowed_denominators, fraction_type_index, like_denominators |
| decimals | dc | Decimal place value, operations | 4-6 | decimal_places, whole_part_max, operation_type |
| geometry_props | gp | Shape properties, angles, classification | 1-10 | shape_complexity, property_type, angle_precision, polygon_sides_max |
| measurement | ms | Length, mass, capacity, time, perimeter, area | 1-7 | measurement_type, value_max, conversion_steps, unit_familiarity |
| data_probability | dp | Tables, graphs, probability, statistics | 1-10 | data_size, value_max, measure_type, probability_complexity |
| compare_order | co | Compare and order numbers | 1-4 | max_number, abstraction_level |
| conceptual | con | Conceptual understanding, definitions | All | abstraction_level, distractor_similarity, context_complexity |

## Dimension Reference

| Dimension | Type | Default Range | Description |
|-----------|------|---------------|-------------|
| max_number | int | 10-1000 | Upper bound for counting |
| skip_interval | choice | [1,2,5,10,20,50,100] | Counting by intervals |
| ordinal_max | int | 10-100 | Highest ordinal position |
| digit_count | int | 2-6 | Number of digits |
| target_place | int | 0-5 | Which place value (0=ones, 1=tens, etc.) |
| operand_max | int | 10-10000 | Maximum operand value |
| regrouping_probability | float | 0.0-1.0 | Probability of carry/borrow |
| step_count | int | 1-3 | Number of operations |
| denominator_max | int | 2-12 | Largest allowed denominator |
| allowed_denominators | choice | [[2,4], [2,3,4,5], [2,3,4,5,6,8], ...] | List of allowed denominators |
| measurement_type | choice | ["length", "mass", "capacity", "time"] | Type of measurement |
| value_max | int | 10-10000 | Maximum measurement value |
| data_size | int | 3-10 | Number of data points |
| shape_complexity | float | 0.0-1.0 | 0=basic shapes, 1=complex polygons |
| abstraction_level | float | 0.0-1.0 | 0=concrete examples, 1=abstract definitions |

## Visual Skeleton Types for Grade 2-3

| Visual Type | Competency Patterns | Grades | MCQ Fallback |
|-------------|---------------------|--------|--------------|
| NumberLine | number line, plot fraction, locate fraction, mark number | 1-6 | Yes |
| BarChart | pictograph, bar graph, present data, interpret graph | 1-6 | No (Visual preferred) |
| ClockSet | read time, write time, clock, hour, elapsed time | 1-4 | Yes |
| PesoMoney | peso, centavo, money, coin, bill, price, cost | 1-5 | Yes |
| GridArea | area, grid, square units, perimeter | 2-5 | Yes |
| SortOrder | order numbers, arrange smallest/largest | 1-4 | No (Visual only) |
| FillInTable | complete table, pattern table, missing table | 1-5 | Yes |
| RuleDiscovery | find pattern, rule pattern, next pattern | 1-4 | Yes |
| Calendar | calendar, days of week, months | 1-3 | Yes |
| Categorize | sort shape, group by, categorize, classify | 1-3 | Yes |

## Summary Statistics

### Grade 2
- **Total Competencies**: 27
- **Fully Covered**: 21 (78%)
- **Partially Covered**: 6 (22%)
- **Not Covered**: 0 (0%)
- **With Visual Option**: 16 (59%)

### Grade 3
- **Total Competencies**: 51
- **Fully Covered**: 36 (71%)
- **Partially Covered**: 15 (29%)
- **Not Covered**: 0 (0%)
- **With Visual Option**: 28 (55%)

### Combined Grade 2-3
- **Total Competencies**: 78
- **Fully Covered**: 57 (73%)
- **Partially Covered**: 21 (27%)
- **Not Covered**: 0 (0%)
- **With Visual Option**: 44 (56%)

---

## Visual Skeleton Reference

### Complete Reference for All Visual Types

#### 1. NumberLine
- **Template Function**: `_gen_number_line()`
- **Key visual_params**:
  - `value`: Target number or fraction to locate
  - `range`: [min, max] - Number line bounds
  - `divisions`: Number of tick marks/divisions
  - `content_type`: "whole_number", "fraction", "decimal", "integer", "addition_visualization", "subtraction_visualization", "fraction_operation"
  - `correct_position`: Index position of correct answer
  - `labels`: Array of endpoint labels ["0", "max"]
  - `is_interactive`: Boolean for interactivity
  - `numerator`/`denominator`: For fractions
  - `show_jumps`: Boolean for showing counting jumps
  - `jump_size`: Size of each jump
  - `start_value`: For addition/subtraction
  - `addend`/`subtrahend`: Operation values
  - `round_to`: For rounding mode ("ten", "hundred", "thousand")
- **Correct answer format**: Integer (position index) or float
- **All_traps structure**:
  - `off_by_one_left`/`off_by_one_right`: Adjacent positions
  - `numerator_only`: Used numerator as position (fractions)
  - `denominator_only`: Used denominator as position (fractions)
  - `larger_denom_larger_value`: Misconception trap
  - `inverted_fraction`: Swapped numerator/denominator
  - `ignore_negative`: Missed negative sign (integers)
  - `negative_magnitude_confusion`: Absolute value confusion
  - `whole_number_decimal_thinking`: Decimal digit confusion
- **Supported question modes**: interactive, mcq, fill_in
- **Invariant checks**: `correct_position` must be within range [0, divisions]

#### 2. ClockSet
- **Template Function**: `_gen_clock_set()`
- **Key visual_params**:
  - `target_time`: Time string (e.g., "3:30" or "15:30")
  - `use_24_hour`: Boolean (Grade 5+ uses 24h)
  - `hours`: Hour value (0-23 or 1-12)
  - `minutes`: Minute value (0-59)
  - `display_hours`: Hour for clock face (1-12)
  - `minute_angle`: Calculated angle for minute hand
  - `hour_angle`: Calculated angle for hour hand
  - `minute_snap_interval`: 5 (snap to 5-minute marks)
- **Correct answer format**: Tuple (hours, minutes) or dictionary
- **All_traps structure**:
  - `hour_minute_swap`: Swapped hour and minute hands
  - `off_by_one_hour_up`/`off_by_one_hour_down`: Hour hand off by one
  - `off_by_five_minutes_up`/`off_by_five_minutes_down`: Minute hand off
  - `hour_hand_rounded`: Hour hand rounded to nearest hour
- **Supported question modes**: interactive (drag hands), mcq, fill_in
- **Invariant checks**: Hours in valid range, minutes 0-59

#### 3. PesoMoney
- **Template Function**: `_gen_peso_money()`
- **Key visual_params**:
  - `target_amount`: Amount to make (positive integer)
  - `available_denominations`: [1, 5, 10, 20, 50, 100, 200, 500, 1000]
  - `greedy_solution`: One valid combination
  - `require_fewest`: Boolean for optimal solution requirement
  - `difficulty_scalar`: 0.0-1.2
  - `problem_type`: "addition", "subtraction", "multiplication", "division", "comparison", "multi_step"
  - Context params: `unit_price`, `quantity`, `total_amount`, `num_people`, etc.
- **Correct answer format**: Integer (target amount) or string
- **All_traps structure**:
  - `overcounted`: Total exceeds target
  - `undercounted`: Total less than target
  - `wrong_denomination_count`: Wrong count of a denomination
  - `doubled_denomination`: Counted one bill/coin twice
- **Supported question modes**: interactive (drag coins/bills), mcq, fill_in
- **Invariant checks**: `target_amount` > 0

#### 4. BarChart
- **Template Function**: `_gen_bar_chart()`
- **Key visual_params**:
  - `labels`: Category names array
  - `values`: Data values array
  - `values2`: Second data series (for double bar)
  - `series_labels`: Labels for multiple series
  - `title`: Chart title
  - `max_y`: Y-axis maximum
  - `scale`: Scale factor (1, 2, 5, 10)
  - `orientation`: "vertical" or "horizontal"
  - `is_pictograph`: Boolean
  - `has_scale`: Boolean (for pictographs)
  - `is_read_mode`: Boolean (READ vs CREATE mode)
  - `is_interactive`: Boolean
  - `ask_category`: Specific category for question
  - `ask_series`: Which series to ask about
- **Correct answer format**: Array of values, or single value, or array of arrays
- **All_traps structure**:
  - `swapped_adjacent`: Two adjacent bars swapped
  - `all_same_height`: All bars at mean height
  - `off_by_grid_line`: Values off by scale amount
  - `doubled_value`: One value doubled
  - `reversed_order`: Bars in reverse order
- **Supported question modes**: interactive (create chart), read_bar, plotter_bar, mcq, fill_in
- **Invariant checks**: All values >= 0, values array length > 0

#### 5. GridArea
- **Template Function**: `_gen_grid_area()`
- **Key visual_params**:
  - `grid_size`: [rows, cols] - Grid dimensions (e.g., [10, 10])
  - `shape_type`: "rectangle", "L_shape", "array", "distribution_grid", "division_model", "symmetry_completion", "translatable_shape", "composite"
  - `width`: Width in grid units (for rectangles)
  - `height`: Height in grid units (for rectangles)
  - `correct_count`: Area, perimeter, or count value
  - `total_objects`: For distribution problems
  - `num_groups`: Number of groups for division
  - `objects_per_group`: Result for distribution
  - `components`: List of component shapes (composite)
  - `initial_position`: Starting coordinates (translation)
  - `translation`: [dx, dy] translation vector
  - `measure_type`: "area" or "perimeter"
- **Correct answer format**: Integer (count/area/perimeter)
- **All_traps structure**:
  - `off_by_few_under`/`off_by_few_over`: Counting errors
  - `counted_perimeter`: Confused area with perimeter
  - `missed_one_row`/`missed_one_column`: Partial counting
- **Supported question modes**: interactive (shade/click squares), mcq, fill_in
- **Invariant checks**: Grid dimensions valid, shape fits in grid

#### 6. SortOrder
- **Template Function**: `_gen_sort_order()`
- **Key visual_params**:
  - `items`: Array of items to sort (numbers or fractions)
  - `correct_sequence`: Sorted array (ascending or descending)
  - `direction`: "ascending" or "descending"
  - `content_type`: "whole", "fraction", "decimal", "integer"
  - `same_denominator`: Boolean (for fractions)
  - `denominator`: Common denominator (if applicable)
- **Correct answer format**: Array of sorted items
- **All_traps structure**:
  - `completely_reversed`: Sorted in opposite direction
  - `adjacent_swap`: Two adjacent items swapped
  - `endpoints_correct_only`: Only first and last correct
- **Supported question modes**: interactive (drag to reorder), mcq, fill_in, ordering
- **Invariant checks**: Items array matches correct_sequence when sorted

#### 7. FillInTable
- **Template Function**: `_gen_fill_in_table()`
- **Key visual_params**:
  - `columns`: Column header names
  - `rows`: 2D array with data (None for blanks)
  - `blank_inputs`: List of positions to fill
  - `correct_fills`: Array of correct values for blanks
  - `rule_description`: Human-readable pattern rule
  - `pattern_type`: "multiplication", "skip_count", "repeating", "linear", "place_value"
- **Correct answer format**: Array of values for blank cells
- **All_traps structure**:
  - `off_by_one_up`/`off_by_one_down`: ±1 errors
  - `added_instead`: Added instead of multiplied
  - `forgot_constant_term`: Missed constant in linear pattern
  - `used_previous`: Copied previous output
- **Supported question modes**: interactive (fill blanks), mcq, fill_in, cloze
- **Invariant checks**: Blank positions valid, correct_fills length matches blanks

#### 8. RuleDiscovery
- **Template Function**: `_gen_rule_discovery()`
- **Key visual_params**:
  - `table`: Array of [input, output] pairs
  - `rule_expression`: Mathematical rule as string (e.g., "3*n+2")
  - `variable_name`: Input variable name ("n")
  - `pattern_type`: "linear", "quadratic", "multiplication"
- **Correct answer format**: String (rule expression)
- **All_traps structure**:
  - `coefficient_off_by_one_up`/`coefficient_off_by_one_down`: Slope errors
  - `constant_off_by_one_up`/`constant_off_by_one_down`: Intercept errors
  - `forgot_constant_term`: Missing constant
  - `swapped_coefficient_and_constant`: Swapped slope and intercept
  - `additive_instead`: Used addition instead of multiplication
  - `constant_rule`: Thought output was constant
- **Supported question modes**: interactive (complete table), mcq, fill_in, expression
- **Invariant checks**: Table has at least 2 rows, rule produces table values

#### 9. Calendar
- **Template Function**: `_gen_calendar()`
- **Key visual_params**:
  - `year`: Calendar year
  - `month`: Month number (1-12)
  - `task_type`: "select_date" or "measure_duration"
  - `correct_date`: Day to select (for select_date)
  - `correct_duration`: Number of days (for measure_duration)
- **Correct answer format**: Integer (day or duration)
- **All_traps structure**:
  - `one_day_before`/`one_day_after`: Off by one day
  - `one_week_before`/`one_week_after`: Off by one week
  - `exclusive_count`: Counted exclusively vs inclusively
  - `off_by_one`: General counting error
- **Supported question modes**: interactive (click dates), mcq, fill_in
- **Invariant checks**: Valid year/month, date in month range

#### 10. Categorize
- **Template Function**: `_gen_categorize()`
- **Key visual_params**:
  - `categories`: Array of category names
  - `items`: Array of items to categorize
  - `correct_categories`: Dictionary mapping items to categories
  - `comparison_type`: "mass_balance", "capacity", "shape_type" (optional)
- **Correct answer format**: Dictionary {item: category}
- **All_traps structure**:
  - `swapped_few_items`: A few items wrong
  - `swapped_many_items`: Many items wrong
  - `all_in_one_category`: All items in first category
- **Supported question modes**: interactive (drag to categories), mcq, fill_in, categorize
- **Invariant checks**: All items have assigned categories

---

## Type Codes Reference

| Code | Visual Type | Use Case |
|------|-------------|----------|
| nl | NumberLine | Fractions, decimals, whole numbers, operations |
| clk | ClockSet | Time reading and elapsed time |
| pm | PesoMoney | Philippine currency problems |
| bc | BarChart | Data representation and interpretation |
| ga | GridArea | Area, perimeter, arrays, division |
| so | SortOrder | Ordering numbers and fractions |
| fit | FillInTable | Pattern tables, place value tables |
| rd | RuleDiscovery | Pattern rules and functions |
| cal | Calendar | Dates and duration |
| cat | Categorize | Sorting and classification |

---

## Question Mode Mapping

| Question Mode | Visual Types | Description |
|---------------|--------------|-------------|
| interactive | All | Student manipulates the visual directly |
| mcq | All | Multiple choice with visual as stimulus |
| fill_in | All | Visual shown, student types answer |
| number_line | NumberLine | Specific to number line problems |
| clock_set | ClockSet | Specific to time problems |
| currency_picker | PesoMoney | Specific to money problems |
| plotter_bar | BarChart | Create bar chart from data |
| read_bar | BarChart | Read values from pre-filled chart |
| grid_area | GridArea | Area/perimeter problems |
| ordering | SortOrder | Ordering problems |
| cloze | FillInTable | Fill-in-the-blank tables |
| expression | RuleDiscovery | Algebraic rule entry |
| calendar | Calendar | Calendar-based problems |
| categorize | Categorize | Classification problems |

---

## MCQ Skeleton Templates (All Sub-Generators)

This section documents every MCQ template function, its stem variations, and trap structures.
Each generator produces deterministic output from a seed and can be regenerated from a skeleton_id.

---

### Measurement Templates (`_gen_measurement`)

#### `_gen_meas_length_convert` — Length Unit Conversion
- **Competencies**: #4, #5
- **Stems**:
  1. "Convert {m} meters to centimeters."
  2. "How many centimeters are in {m} meters?"
  3. "{m} m = ___ cm"
- **Traps**:
  - `ms_wrong_factor`: Used ×10 instead of ×100
  - `ms_wrong_factor`: Used ×1000 instead of ×100
  - `ms_no_convert`: Gave original value unchanged
- **Example**: "Convert 5 meters to centimeters." → 500 (traps: 50, 5000, 5)

#### `_gen_meas_unit_selection` — Choose Appropriate Unit
- **Competencies**: #5
- **Stems**:
  1. "Which unit is better for measuring the length of {obj}: meters or centimeters?"
  2. "To measure {obj}, should you use meters (m) or centimeters (cm)?"
  3. "The most appropriate unit for measuring {obj} is:"
- **Objects (cm)**: a pencil (15), an eraser (5), a book (25), a hand span (20), a crayon (10), a spoon (18)
- **Objects (m)**: a classroom (8), a swimming pool (25), a basketball court (28), a hallway (15), a flagpole (10), a school bus (12)
- **Traps**:
  - `ms_wrong_unit`: Chose the wrong unit
  - `ms_unit_too_big`: kilometers
  - `ms_unit_too_small`: millimeters
- **Example**: "Which unit is better for measuring the length of a pencil: meters or centimeters?" → centimeters

#### `_gen_meas_compare` — Compare Lengths Requiring Conversion
- **Competencies**: #4
- **Stems**:
  1. "Which is longer: {a} {unit_a} or {b} {unit_b}?"
  2. "Compare: {a} {unit_a} and {b} {unit_b}. Which is greater?"
  3. "A ribbon is {a} {unit_a} long. A rope is {b} {unit_b} long. Which is longer?"
- **Traps**:
  - `ms_no_convert`: Compared digits without converting
  - `ms_wrong_equal`: Said they are equal when not
  - `ms_no_answer`: Said cannot tell
- **Example**: "Which is longer: 213 cm or 1 m?" → 213 cm

#### `_gen_meas_word_problem` — Length/Distance Word Problems
- **Competencies**: #7
- **Addition Stems**:
  1. "A path is {a} {unit} long. Another path is {b} {unit} long. What is the total distance?"
  2. "A piece of string is {a} {unit}. Another piece is {b} {unit}. How long are they together?"
  3. "You walk {a} {unit} then {b} {unit} more. How far did you walk in total?"
- **Subtraction Stems**:
  1. "A rope is {total} {unit} long. You cut off {part} {unit}. How much is left?"
  2. "A board is {total} {unit}. After cutting {part} {unit}, what length remains?"
  3. "You have {total} {unit} of ribbon. You use {part} {unit}. How much is left?"
- **Traps (add)**: `ms_wrong_op` (subtracted), `ms_off_by` (off by 10), `ms_partial` (gave one operand)
- **Traps (sub)**: `ms_wrong_op` (added), `ms_off_one`, `ms_partial`

#### `_gen_meas_perimeter` — Perimeter of Shapes
- **Competencies**: #12, #13, #14
- **Square Stems (find perimeter)**:
  1. "Find the perimeter of a square with side length {s} cm."
  2. "A square has sides of {s} cm each. What is its perimeter?"
  3. "What is the perimeter of a square with side = {s} cm?"
- **Square Stems (find side from perimeter)**:
  1. "A square has a perimeter of {p} cm. What is the length of one side?"
  2. "The perimeter of a square is {p} cm. Find the side length."
  3. "If a square's perimeter is {p} cm, each side measures ___ cm."
- **Rectangle Stems (find perimeter)**:
  1. "Find the perimeter of a rectangle with length {l} cm and width {w} cm."
  2. "A rectangle is {l} cm long and {w} cm wide. What is its perimeter?"
  3. "What is the perimeter of a rectangle: L = {l} cm, W = {w} cm?"
- **Rectangle Stems (find missing side)**:
  1. "A rectangle has a perimeter of {p} cm and a length of {l} cm. Find the width."
  2. "The perimeter of a rectangle is {p} cm. One side is {l} cm. What is the other side?"
  3. "Perimeter = {p} cm, length = {l} cm. Width = ?"
- **Triangle Stems**:
  1. "A triangle has sides of {a} cm, {b} cm, and {c} cm. What is its perimeter?"
  2. "Find the perimeter of a triangle with sides {a}, {b}, and {c} cm."
  3. "The sides of a triangle measure {a} cm, {b} cm, and {c} cm. Perimeter = ?"
- **Traps**: `ms_used_area`, `ms_only_two_sides`, `ms_forgot_side`, `ms_only_once`, `ms_div_by_2`

#### `_gen_meas_area` — Area of Squares and Rectangles (Grade 3+)
- **Competencies**: #54, #55, #56, #57
- **Square Stems**:
  1. "Find the area of a square with side length {s} cm."
  2. "A square has sides of {s} cm. What is its area in {unit}?"
  3. "What is the area of a square with side = {s}?"
- **Square Word Problem Stems**:
  1. "A garden is shaped like a square with sides of {s} m. How many square meters of soil are needed to cover it?"
  2. "A square room has sides of {s} m. How much carpet is needed to cover the floor?"
  3. "A square tile has sides of {s} cm. What is its area?"
- **Rectangle Stems**:
  1. "Find the area of a rectangle with length {l} cm and width {w} cm."
  2. "A rectangle is {l} cm long and {w} cm wide. What is its area?"
  3. "What is the area? Length = {l}, Width = {w}."
- **Rectangle Word Problem Stems**:
  1. "A room is {l} m long and {w} m wide. How many square meters of carpet are needed?"
  2. "A rectangular garden is {l} m by {w} m. What is its area?"
  3. "A wall is {l} m wide and {w} m tall. How much paint is needed to cover it?"
- **Traps**: `ms_used_perimeter` (2*(l+w)), `ms_added_not_mult` (l+w), `ms_doubled_not_squared` (s*2), `ms_off_by_side`

#### `_gen_meas_mass` — Mass Measurement and Conversion
- **Competencies**: #61, #62, #63
- **Conversion Stems (kg→g)**:
  1. "Convert {kg} kg to grams."
  2. "How many grams are in {kg} kg?"
  3. "{kg} kg = ___ g"
- **Conversion Stems (g→kg)**:
  1. "Convert {g} g to kilograms."
  2. "How many kilograms is {g} g?"
  3. "{g} g = ___ kg"
- **Comparison Stems**:
  1. "Which is heavier: {kg} kg or {g} g?"
  2. "Compare: {kg} kg and {g} g. Which has more mass?"
  3. "A bag weighs {kg} kg. A box weighs {g} g. Which is heavier?"
- **Estimation Stems**:
  1. "About how much does {obj} weigh?"
  2. "Estimate the mass of {obj}."
  3. "Which is the best estimate for the mass of {obj}?"
- **Estimation Objects**: apple (150g), pencil (10g), textbook (500g), coin (5g), bicycle (12kg), bag of rice (5kg), chair (8kg)
- **Traps**: `ms_wrong_factor`, `ms_no_convert`, `ms_est_too_high`, `ms_est_too_low`, `ms_wrong_unit`

#### `_gen_meas_capacity` — Capacity Measurement and Conversion
- **Competencies**: #64, #65, #66
- **Conversion Stems (L→mL)**:
  1. "How many milliliters are in {L} liters?"
  2. "Convert {L} L to mL."
  3. "{L} L = ___ mL"
- **Conversion Stems (mL→L)**:
  1. "Convert {mL} mL to liters."
  2. "How many liters is {mL} mL?"
  3. "{mL} mL = ___ L"
- **Comparison Stems**:
  1. "Which holds more: {L} L or {mL} mL?"
  2. "Compare: a jug with {L} L and a bottle with {mL} mL. Which has more?"
  3. "Container A: {L} L. Container B: {mL} mL. Which holds more?"
- **Estimation Stems**:
  1. "About how much does {obj} hold?"
  2. "Estimate the capacity of {obj}."
  3. "Which is the best estimate for {obj}?"
- **Estimation Objects**: glass of water (250mL), bucket (10L), teaspoon (5mL), bathtub (150L), water bottle (500mL), fish tank (40L)
- **Traps**: `ms_wrong_factor`, `ms_no_convert`, `ms_est_too_high`, `ms_est_too_low`, `ms_wrong_unit`

#### `_gen_meas_time` — Duration and Elapsed Time
- **Competencies**: #8, #9, #10
- **Calendar Duration Stems**:
  1. "How many days are there from {start_day} to {end_day}?"
  2. "An event starts on {start_day} and ends on {end_day}. How many days is that?"
  3. "Count the days from {start_day} to {end_day} (not including {start_day})."
- **Elapsed Time Stems**:
  1. "A movie starts at {start_time} and lasts {elapsed} minutes. When does it end?"
  2. "You begin reading at {start_time}. After {elapsed} minutes, what time is it?"
  3. "Class starts at {start_time} and is {elapsed} minutes long. What time does it end?"
- **General Time Facts**:
  - "How many minutes are in 1 hour?" → 60
  - "How many hours are in 1 day?" → 24
  - "How many days are in 1 week?" → 7
  - "How many minutes are in 2 hours?" → 120
  - "How many days are in 2 weeks?" → 14
- **Traps**: `ms_inclusive_count`, `ms_off_one`, `ms_complement`, `ms_time_no_min`, `ms_time_no_carry`, `ms_half`, `ms_confused_unit`

#### `_gen_meas_estimation` — Estimate Real-World Measurements
- **Competencies**: #6, #62, #65
- **Stems**:
  1. "Which is the best estimate for the length of {obj}?"
  2. "About how long is {obj}?"
  3. "Estimate: The length of {obj} is closest to:"
- **Objects**: door's height (2m), pencil (18cm), classroom (10m), finger width (1cm), car (4m), table height (75cm), ant (3mm), basketball court (28m)
- **Traps**: `ms_est_too_high`, `ms_est_too_low`, `ms_wrong_unit`

---

### Geometry Templates (`_gen_geometry_props`)

#### `_gen_geo_circles` — Circles, Half Circles, Quarter Circles
- **Competencies**: #1
- **Question Bank** (6 templates, 3 stems each):
  1. "How many straight edges does a circle have?" → 0
  2. "How many straight edges does a half circle have?" → 1
  3. "How many straight edges does a quarter circle have?" → 2
  4. "Which shape has NO straight edges?" → circle
  5. "A quarter circle looks like a slice of:" → pizza slice
  6. "How many curved edges does a half circle have?" → 1
- **Traps**: `gp_curve_as_side`, `gp_forgot_diameter`, `gp_forgot_one`, `gp_has_diameter`, `gp_has_radii`

#### `_gen_geo_compose_shapes` — Compose/Decompose Composite Figures
- **Competencies**: #2
- **Question Bank** (8 templates, 3 stems each):
  1. "Two triangles can be put together to make a:" → rectangle
  2. "A rectangle can be cut into two equal:" → triangles
  3. "Four small squares can be arranged to make a:" → larger square
  4. "How many triangles can a square be divided into by cutting both diagonals?" → 4
  5. "A square and a triangle placed side by side can look like a:" → house (pentagon)
  6. "Two rectangles placed end-to-end make a:" → longer rectangle
  7. "An L-shape can be decomposed into:" → 2 rectangles
  8. "How many squares make up a 2x3 rectangle?" → 6
- **Traps**: `gp_wrong_shape`, `gp_same_shape`, `gp_one_diagonal`, `gp_too_many_sides`, `gp_too_few`

#### `_gen_geo_translations` — Slides (Translations) on Grid
- **Competencies**: #3, #67
- **Single-Direction Stems**:
  1. "A shape is at ({x}, {y}). It slides {d} units {dir}. Where is it now?"
  2. "Start at position ({x}, {y}). Move {d} squares {dir}. New position?"
  3. "After sliding {d} units {dir} from ({x}, {y}), the shape is at:"
- **Two-Direction Stems**:
  1. "A shape is at ({x}, {y}). It slides {dx} units {dir_h} and {dy} units {dir_v}. Where is it now?"
  2. "Start at ({x}, {y}). Move {dx} {dir_h}, then {dy} {dir_v}. New position?"
  3. "Translate the point ({x}, {y}) by {dx} {dir_h} and {dy} {dir_v}. Result?"
- **Traps**: `gp_wrong_direction`, `gp_moved_both_axes`, `gp_no_move`, `gp_ignored_direction`, `gp_swapped_xy`

#### `_gen_geo_line_types` — Point, Line, Line Segment, Ray
- **Competencies**: #58
- **Question Bank** (6 templates, 3 stems each):
  1. "Which has exactly two endpoints?" → line segment
  2. "Which extends forever in ONE direction from a single point?" → ray
  3. "Which extends forever in BOTH directions?" → line
  4. "Which has no length, width, or height?" → point
  5. "How many endpoints does a ray have?" → 1
  6. "How many endpoints does a line have?" → 0
- **Traps**: `gp_one_endpoint`, `gp_no_endpoints`, `gp_both_directions`, `gp_has_endpoints`, `gp_confused_segment`, `gp_confused_ray`

#### `_gen_geo_line_relations` — Parallel, Intersecting, Perpendicular
- **Competencies**: #59
- **Question Bank** (6 templates, 3 stems each):
  1. "Lines that never meet (no matter how far extended) are called:" → parallel
  2. "Lines that cross at a right angle (90 degrees) are called:" → perpendicular
  3. "Lines that cross at any point are called:" → intersecting
  4. "Which is an example of parallel lines?" → opposite edges of a ruler
  5. "Are perpendicular lines also intersecting?" → yes, they intersect at 90 degrees
  6. "The plus sign (+) shows two lines that are:" → perpendicular
- **Traps**: `gp_perp_parallel`, `gp_parallel_perp`, `gp_inter_parallel`, `gp_too_general`, `gp_too_specific`

#### `_gen_geo_symmetry` — Line Symmetry
- **Competencies**: #68, #69
- **Question Bank** (8 templates, 3 stems each):
  1. "How many lines of symmetry does a square have?" → 4
  2. "How many lines of symmetry does a rectangle (not square) have?" → 2
  3. "How many lines of symmetry does an equilateral triangle have?" → 3
  4. "Does a scalene triangle have any lines of symmetry?" → 0
  5. "How many lines of symmetry does a circle have?" → infinite
  6. "Which letter has exactly one line of symmetry: A, H, S, or N?" → A
  7. "Which shape does NOT have line symmetry?" → a parallelogram (not rectangle)
  8. "To complete a symmetric figure, you create a ___." → mirror image of the left
- **Traps**: `gp_only_hv`, `gp_only_one`, `gp_thought_square`, `gp_assumed_one`, `gp_not_reflected`

#### `_gen_geo_surfaces` — Straight/Curved Lines, Flat/Curved Surfaces
- **Competencies**: #11
- **Question Bank** (8 templates, 3 stems each):
  1. "How many flat surfaces does a sphere (ball) have?" → 0
  2. "How many flat surfaces does a cylinder (can) have?" → 2
  3. "How many curved surfaces does a cylinder have?" → 1
  4. "How many curved surfaces does a cube have?" → 0
  5. "A cone has how many flat surface(s)?" → 1
  6. "Which 3D shape has ONLY flat surfaces?" → cube
  7. "The edge of a coin is an example of a:" → curved line
  8. "The edge of a ruler is an example of a:" → straight line
- **Traps**: `gp_one_face`, `gp_forgot_bottom`, `gp_only_curved`, `gp_counted_flat`, `gp_wrong_type`

#### `_gen_geo_compare_shapes` — Compare Shapes by Properties
- **Competencies**: #1 (Grade 1-2 shape recognition)
- **Stems**:
  1. "Which shape has more sides: a {shape1} or a {shape2}?"
  2. "Between a {shape1} and a {shape2}, which has more sides?"
  3. "Compare: Does a {shape1} or {shape2} have more sides?"
  4. "Which shape has more corners: a {shape1} or a {shape2}?"
  5. "Between a {shape1} and a {shape2}, which has more corners (vertices)?"
  6. "Compare corners: {shape1} vs {shape2}. Which has more?"
- **Shape Pool**: triangle (3), square (4), rectangle (4), pentagon (5), hexagon (6), circle (0)
- **Traps**: `gp_wrong_compare`, `gp_wrong_equal`, `gp_no_answer`

#### `_gen_geo_identify` — Identify Shapes by Properties
- **Stems**:
  1. "Which shape has {n} sides and {n} corners?"
  2. "Name the shape with exactly {n} sides."
  3. "A shape with {n} straight sides is called a:"
- **Traps**: `gp_wrong_shape` (3 other shapes from pool)

#### `_gen_geo_properties_default` — Count Sides/Corners
- **Stems (sides)**:
  1. "How many sides does a {shape} have?"
  2. "Count the sides of a {shape}."
  3. "A {shape} has ___ sides."
- **Stems (corners)**:
  1. "How many corners (vertices) does a {shape} have?"
  2. "Count the corners of a {shape}."
  3. "A {shape} has ___ corners."
- **Traps**: `gp_off_one_up`, `gp_off_one_down`, `gp_wrong_shape_sides`, `gp_doubled`

---

### Arithmetic Templates (New Branches)

#### `_gen_arithmetic_estimate` — Estimation by Rounding
- **Competencies**: #79, #82, #88, #96
- **Stems**:
  1. "Estimate {a} {op} {b} by rounding to the nearest {round_to}."
  2. "Round each number to the nearest {round_to}, then compute: {a} {op} {b}."
  3. "What is the best estimate for {a} {op} {b}?"
- **Operations**: add (+), subtract (-), multiply (x), divide (/)
- **Rounding Rules**: operand_max ≤ 100 → round to 10; ≤ 1000 → round to 100; else → round to 1000
- **Traps**: `ar_exact_not_estimate` (gave exact answer), `ar_rounded_wrong` (rounded incorrectly), `ar_off_by_round` (off by one rounding unit)
- **Example**: "Estimate 487 + 312 by rounding to the nearest hundred." → 800 (500+300)

#### `_gen_arithmetic_even_odd` — Even/Odd Identification
- **Competencies**: #44
- **Identify Stems**:
  1. "Is {n} even or odd?"
  2. "The number {n} is:"
  3. "Classify {n}: even or odd?"
- **Which-Is Stems**:
  1. "Which number is {even/odd}?"
  2. "Identify the {even/odd} number:"
  3. "Select the {even/odd} number from the choices."
- **Division Rule Stems**:
  1. "Why is {n} an even number?"
  2. "{n} is even because:"
  3. "How do we know {n} is even?"
- **Traps**: `ar_even_odd_swap`, `ar_no_category`, `ar_partial_rule`, `ar_wrong_rule`, `ar_opposite`
- **Example**: "Is 37 even or odd?" → odd

---

### Counting Templates (New Branch)

#### `_gen_counting_pattern` — Number Patterns and Sequences
- **Competencies**: #34, #35, #90, #91
- **Arithmetic Pattern Stems**:
  1. "What comes next? {n1}, {n2}, {n3}, {n4}, ___"
  2. "Find the next number in the pattern: {seq}, ___"
  3. "Continue the pattern: {seq}, ___"
- **Skip Count Pattern Stems**:
  1. "What comes next? {seq}, ___"
  2. "Count by {skip}s: {seq}, ___"
  3. "The pattern is: {seq}. What is next?"
- **Doubling Pattern Stems**:
  1. "What comes next? {seq}, ___"
  2. "Find the pattern: {seq}, ___"
  3. "Each number doubles. Continue: {seq}, ___"
- **Pattern Types**: arithmetic (constant difference), skip_count (2s, 5s, 10s, etc.), doubling
- **Supports**: increasing and decreasing patterns
- **Traps**: `cnt_off_by_one`, `cnt_skipped_one`, `cnt_wrong_direction`, `cnt_wrong_interval`, `cnt_wrong_rule`, `cnt_added_prev`
- **Example**: "What comes next? 5, 10, 15, 20, ___" → 25

---

### Place Value Templates (New Branches)

#### `_gen_pv_round` — Rounding Numbers
- **Competencies**: #74
- **Stems**:
  1. "Round {number} to the nearest {place}."
  2. "What is {number} rounded to the nearest {place}?"
  3. "{number} rounded to the nearest {place} is:"
- **Places**: ten, hundred, thousand
- **Auto-adjusts digit_count**: Rounding to thousands requires at least 4-digit numbers
- **Traps**: `pv_rounded_wrong_dir` (rounded wrong way), `pv_wrong_place` (rounded to wrong place value), `pv_no_round` (gave original number)
- **Example**: "Round 4,567 to the nearest hundred." → 4,600

#### `_gen_pv_read_write` — Read/Write Numbers in Words
- **Competencies**: #16, #71
- **Words→Numeral Stems**:
  1. "Write '{words}' as a numeral."
  2. "What number is '{words}'?"
  3. "'{words}' in digits is:"
- **Numeral→Words Stems**:
  1. "Write {number} in words."
  2. "How do you write {number} in words?"
  3. "The number {number} written in words is:"
- **Handles**: ones, teens, tens, hundreds, thousands
- **Traps**: `pv_misplaced_digit`, `pv_wrong_value`, `pv_reversed`, `pv_wrong_words`, `pv_wrong_place_words`
- **Example**: "Write 'three hundred twenty-five' as a numeral." → 325

---

### Compare/Order Templates (Rebuilt)

#### `_gen_compare_symbol` — Fill In Comparison Symbol
- **Competencies**: #75
- **Stems**:
  1. "Fill in the blank: {a} ___ {b}"
  2. "Compare: {a} ___ {b}. Use >, <, or =."
  3. "Which symbol goes between {a} and {b}?"
- **Answers**: >, <, = (15% chance of equal values)
- **Traps**: `co_wrong_symbol` (each of the other two symbols), >= (common misconception)
- **Example**: "Fill in the blank: 5,432 ___ 5,342" → >

#### `_gen_compare_ordering_mcq` — Order Numbers (MCQ Fallback)
- **Competencies**: #19, #76
- **Stems**:
  1. "Arrange from {direction}: {shuffled numbers}"
  2. "Order these numbers from {direction}: {shuffled numbers}"
  3. "Put in order ({direction}): {shuffled numbers}"
- **Directions**: smallest to largest, largest to smallest
- **Traps**: `co_reversed` (complete reverse), `co_middle_swap` (adjacent pair swapped), `co_endpoint_swap` (first/last swapped)
- **Example**: "Arrange from smallest to largest: 456, 128, 702, 389" → "128, 389, 456, 702"

#### `_gen_compare_which_greater` — Which Number Is Greater
- **Competencies**: #19, #75
- **Stems**:
  1. "Which number is greater: {a} or {b}?"
  2. "Compare {a} and {b}. Which is larger?"
  3. "Which is bigger: {a} or {b}?"
- **Traps**: `co_lesser` (the smaller number), `co_sum` (added them), `co_diff` (subtracted them)

---

### Trap Catalog (New Traps Added)

| Trap Code | Name | Description |
|-----------|------|-------------|
| `ms_wrong_factor` | Wrong Conversion Factor | Used ×10 or ×1000 instead of ×100 |
| `ms_no_convert` | No Conversion | Gave the original value unchanged |
| `ms_wrong_unit` | Wrong Unit | Selected inappropriate unit for object |
| `ms_unit_too_big` | Unit Too Large | Used km when cm needed |
| `ms_unit_too_small` | Unit Too Small | Used mm when m needed |
| `ms_no_convert` | Didn't Convert | Compared raw digits across units |
| `ms_wrong_equal` | Incorrect Equality | Said unequal values are equal |
| `ms_wrong_op` | Wrong Operation | Added when should subtract, or vice versa |
| `ms_off_one` | Off By One | Counted one too many or too few |
| `ms_partial` | Partial Answer | Gave one operand instead of result |
| `ms_used_area` | Used Area Formula | Computed L×W instead of 2(L+W) |
| `ms_only_once` | Only Added Once | Computed L+W not 2(L+W) |
| `ms_used_perimeter` | Used Perimeter | Computed 2(L+W) instead of L×W |
| `ms_added_not_mult` | Added Not Multiplied | Computed L+W instead of L×W |
| `ms_inclusive_count` | Inclusive Count Error | Off by one in day counting |
| `ms_time_no_carry` | No Minute Carry | Didn't carry minutes to hours |
| `ms_est_too_high` | Estimate Too High | Overestimated by ×10 |
| `ms_est_too_low` | Estimate Too Low | Underestimated by ÷10 |
| `gp_curve_as_side` | Counted Curve | Counted curved edge as a straight side |
| `gp_forgot_diameter` | Forgot Diameter | Didn't count the flat edge of semicircle |
| `gp_wrong_direction` | Wrong Direction | Moved shape the wrong way |
| `gp_swapped_xy` | Swapped X and Y | Confused horizontal and vertical |
| `gp_no_move` | No Movement | Gave original position |
| `gp_one_endpoint` | One Endpoint | Confused line segment with ray |
| `gp_both_directions` | Both Directions | Confused ray with line |
| `gp_perp_parallel` | Perpendicular↔Parallel | Swapped definitions |
| `gp_only_hv` | Only H/V | Counted only horizontal/vertical symmetry lines |
| `gp_not_reflected` | Not Reflected | Copied instead of mirroring |
| `ar_exact_not_estimate` | Exact Not Estimate | Computed exact answer instead of estimating |
| `ar_even_odd_swap` | Even/Odd Swap | Classified even as odd or vice versa |
| `pv_rounded_wrong_dir` | Rounded Wrong Direction | Rounded up when should round down |
| `pv_misplaced_digit` | Misplaced Digit | Wrote digits in wrong place value |
| `co_wrong_symbol` | Wrong Symbol | Used < instead of > or vice versa |
| `co_reversed` | Completely Reversed | Gave opposite ordering |
| `co_middle_swap` | Middle Pair Swap | Swapped two adjacent items |
| `cnt_off_by_one` | Pattern Off By One | Added 1 instead of the pattern step |
| `cnt_skipped_one` | Skipped A Term | Jumped ahead two steps |
| `cnt_wrong_direction` | Wrong Pattern Direction | Continued opposite direction |

---

*Updated: June 2025*
*Source files: matatagmath.json, matatag_skeletons.py, visual_skeletons.py*
*All templates verified against generators with deterministic seed testing*
