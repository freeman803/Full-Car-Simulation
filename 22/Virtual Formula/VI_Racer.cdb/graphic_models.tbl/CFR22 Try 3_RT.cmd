!
!-------------------------- Default Units for Model ---------------------------!
!
!
defaults units  &
   length = mm  &
   angle = deg  &
   force = newton  &
   mass = kg  &
   time = sec
!
defaults units  &
   coordinate_system_type = cartesian  &
   orientation_type = body313
!
!------------------------ Default Attributes for Model ------------------------!
!
!
defaults attributes  &
   inheritance = bottom_up  &
   icon_visibility = on  &
   grid_visibility = off  &
   size_of_icons = 50.0  &
   spacing_for_grid = 50.0
!
!------------------------------ Adams/View Model ------------------------------!
!
!
model create  &
   model_name = CFR22 Try 3_RT  &
   title = "ADAMS/Car template"
!
view erase
!
!-------------------------------- Data storage --------------------------------!
!
!
data_element create string  &
   string_name = .CFR22 Try 3_RT.minor_role_string  &
   string = ""
!
!--------------------------------- Materials ----------------------------------!
!
!
material create  &
   material_name = .CFR22 Try 3_RT.steel  &
   youngs_modulus = 2.07E+005  &
   poissons_ratio = 0.29  &
   density = 7.801E-006
!
!-------------------------------- Rigid Parts ---------------------------------!
!
! Create parts and their dependent markers and graphics
!
!----------------------------------- ground -----------------------------------!
!
!
! ****** Ground Part ******
!
defaults model  &
   part_name = ground
!
defaults coordinate_system  &
   default_coordinate_system = .CFR22 Try 3_RT.ground
!
! ****** Markers for current part ******
!
marker create  &
   marker_name = .CFR22 Try 3_RT.ground.origo  &
   location = 0.0, 0.0, 0.0  &
   orientation = 0.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .CFR22 Try 3_RT.ground.origo  &
   visibility = off  &
   name_visibility = off
!
marker create  &
   marker_name = .CFR22 Try 3_RT.ground.shell_Ref  &
   location = 0.0, 0.0, -345.0  &
   orientation = 0.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .CFR22 Try 3_RT.ground.shell_Ref  &
   visibility = off  &
   name_visibility = off
!
!-------------------------------- ges_chassis ---------------------------------!
!
!
defaults coordinate_system  &
   default_coordinate_system = .CFR22 Try 3_RT.ground
!
part create rigid_body name_and_position  &
   part_name = .CFR22 Try 3_RT.ges_chassis  &
   adams_id = 2  &
   location = 0.0, 0.0, 0.0  &
   orientation = 0.0d, 0.0d, 0.0d
!
defaults coordinate_system  &
   default_coordinate_system = .CFR22 Try 3_RT.ges_chassis
!
! ****** Markers for current part ******
!
marker create  &
   marker_name = .CFR22 Try 3_RT.ges_chassis.cm  &
   location = 1500.0, 0.0, 300.0  &
   orientation = 0.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .CFR22 Try 3_RT.ges_chassis.cm  &
   visibility = off  &
   name_visibility = off
!
marker create  &
   marker_name = .CFR22 Try 3_RT.ges_chassis.inertia_frame  &
   location = 1500.0, 0.0, 300.0  &
   orientation = 0.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .CFR22 Try 3_RT.ges_chassis.inertia_frame  &
   visibility = off  &
   name_visibility = off
!
marker create  &
   marker_name = .CFR22 Try 3_RT.ges_chassis.fwl  &
   location = 0.0, 760.0, 329.0  &
   orientation = 0.0d, 90.0d, 0.0d
!
marker attributes  &
   marker_name = .CFR22 Try 3_RT.ges_chassis.fwl  &
   visibility = off  &
   name_visibility = off
!
marker create  &
   marker_name = .CFR22 Try 3_RT.ges_chassis.rwl  &
   location = -2777.2, 797.0, 379.28  &
   orientation = 0.0d, 90.0d, 0.0d
!
marker attributes  &
   marker_name = .CFR22 Try 3_RT.ges_chassis.rwl  &
   visibility = off  &
   name_visibility = off
!
marker create  &
   marker_name = .CFR22 Try 3_RT.ges_chassis.rwr  &
   location = -2777.2, -797.0, 379.28  &
   orientation = 0.0d, 90.0d, 0.0d
!
marker attributes  &
   marker_name = .CFR22 Try 3_RT.ges_chassis.rwr  &
   visibility = off  &
   name_visibility = off
!
marker create  &
   marker_name = .CFR22 Try 3_RT.ges_chassis.fwr  &
   location = 0.0, -760.0, 329.0  &
   orientation = 0.0d, 90.0d, 0.0d
!
marker attributes  &
   marker_name = .CFR22 Try 3_RT.ges_chassis.fwr  &
   visibility = off  &
   name_visibility = off
!
part create rigid_body mass_properties  &
   part_name = .CFR22 Try 3_RT.ges_chassis  &
   mass = 1.0  &
   center_of_mass_marker = .CFR22 Try 3_RT.ges_chassis.cm  &
   inertia_marker = .CFR22 Try 3_RT.ges_chassis.inertia_frame  &
   ixx = 1.0  &
   iyy = 1.0  &
   izz = 1.0  &
   ixy = 0.0  &
   izx = 0.0  &
   iyz = 0.0
!
part attributes  &
   part_name = .CFR22 Try 3_RT.ges_chassis  &
   visibility = on  &
   name_visibility = on
!
!------------------------------ whl_front_wheel -------------------------------!
!
!
defaults coordinate_system  &
   default_coordinate_system = .CFR22 Try 3_RT.ground
!
part create rigid_body name_and_position  &
   part_name = .CFR22 Try 3_RT.whl_front_wheel  &
   adams_id = 3  &
   location = 0.0, 760.0, 329.0  &
   orientation = 0.0d, 0.0d, 0.0d
!
defaults coordinate_system  &
   default_coordinate_system = .CFR22 Try 3_RT.whl_front_wheel
!
! ****** Markers for current part ******
!
marker create  &
   marker_name = .CFR22 Try 3_RT.whl_front_wheel.cm  &
   location = 0.0, 0.0, 0.0  &
   orientation = 0.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .CFR22 Try 3_RT.whl_front_wheel.cm  &
   visibility = off  &
   name_visibility = off
!
marker create  &
   marker_name = .CFR22 Try 3_RT.whl_front_wheel.tire_i  &
   location = 0.0, 0.0, 0.0  &
   orientation = 0.0d, 90.0d, 0.0d
!
marker attributes  &
   marker_name = .CFR22 Try 3_RT.whl_front_wheel.tire_i  &
   visibility = off  &
   name_visibility = off
!
part create rigid_body mass_properties  &
   part_name = .CFR22 Try 3_RT.whl_front_wheel  &
   mass = 1.0  &
   center_of_mass_marker = .CFR22 Try 3_RT.whl_front_wheel.cm  &
   ixx = 1.0  &
   iyy = 1.0  &
   izz = 1.0  &
   ixy = 0.0  &
   izx = 0.0  &
   iyz = 0.0
!
part attributes  &
   part_name = .CFR22 Try 3_RT.whl_front_wheel  &
   visibility = on  &
   name_visibility = on
!
!------------------------------ whr_front_wheel -------------------------------!
!
!
defaults coordinate_system  &
   default_coordinate_system = .CFR22 Try 3_RT.ground
!
part create rigid_body name_and_position  &
   part_name = .CFR22 Try 3_RT.whr_front_wheel  &
   adams_id = 5  &
   location = 0.0, -760.0, 329.0  &
   orientation = 0.0d, 0.0d, 0.0d
!
defaults coordinate_system  &
   default_coordinate_system = .CFR22 Try 3_RT.whr_front_wheel
!
! ****** Markers for current part ******
!
marker create  &
   marker_name = .CFR22 Try 3_RT.whr_front_wheel.cm  &
   location = 0.0, 0.0, 0.0  &
   orientation = 0.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .CFR22 Try 3_RT.whr_front_wheel.cm  &
   visibility = off  &
   name_visibility = off
!
marker create  &
   marker_name = .CFR22 Try 3_RT.whr_front_wheel.tire_i  &
   location = 0.0, 0.0, 0.0  &
   orientation = 0.0d, 90.0d, 0.0d
!
marker attributes  &
   marker_name = .CFR22 Try 3_RT.whr_front_wheel.tire_i  &
   visibility = off  &
   name_visibility = off
!
part create rigid_body mass_properties  &
   part_name = .CFR22 Try 3_RT.whr_front_wheel  &
   mass = 1.0  &
   center_of_mass_marker = .CFR22 Try 3_RT.whr_front_wheel.cm  &
   ixx = 1.0  &
   iyy = 1.0  &
   izz = 1.0  &
   ixy = 0.0  &
   izx = 0.0  &
   iyz = 0.0
!
part attributes  &
   part_name = .CFR22 Try 3_RT.whr_front_wheel  &
   visibility = on  &
   name_visibility = on
!
!------------------------------- whl_rear_wheel -------------------------------!
!
!
defaults coordinate_system  &
   default_coordinate_system = .CFR22 Try 3_RT.ground
!
part create rigid_body name_and_position  &
   part_name = .CFR22 Try 3_RT.whl_rear_wheel  &
   adams_id = 4  &
   location = -2777.2, 797.0, 379.28  &
   orientation = 0.0d, 0.0d, 0.0d
!
defaults coordinate_system  &
   default_coordinate_system = .CFR22 Try 3_RT.whl_rear_wheel
!
! ****** Markers for current part ******
!
marker create  &
   marker_name = .CFR22 Try 3_RT.whl_rear_wheel.cm  &
   location = 0.0, 0.0, 0.0  &
   orientation = 0.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .CFR22 Try 3_RT.whl_rear_wheel.cm  &
   visibility = off  &
   name_visibility = off
!
marker create  &
   marker_name = .CFR22 Try 3_RT.whl_rear_wheel.tire_i  &
   location = 0.0, 0.0, 0.0  &
   orientation = 0.0d, 90.0d, 0.0d
!
marker attributes  &
   marker_name = .CFR22 Try 3_RT.whl_rear_wheel.tire_i  &
   visibility = off  &
   name_visibility = off
!
part create rigid_body mass_properties  &
   part_name = .CFR22 Try 3_RT.whl_rear_wheel  &
   mass = 1.0  &
   center_of_mass_marker = .CFR22 Try 3_RT.whl_rear_wheel.cm  &
   ixx = 1.0  &
   iyy = 1.0  &
   izz = 1.0  &
   ixy = 0.0  &
   izx = 0.0  &
   iyz = 0.0
!
part attributes  &
   part_name = .CFR22 Try 3_RT.whl_rear_wheel  &
   visibility = on  &
   name_visibility = on
!
!------------------------------- whr_rear_wheel -------------------------------!
!
!
defaults coordinate_system  &
   default_coordinate_system = .CFR22 Try 3_RT.ground
!
part create rigid_body name_and_position  &
   part_name = .CFR22 Try 3_RT.whr_rear_wheel  &
   adams_id = 6  &
   location = -2777.2, -797.0, 379.28  &
   orientation = 0.0d, 0.0d, 0.0d
!
defaults coordinate_system  &
   default_coordinate_system = .CFR22 Try 3_RT.whr_rear_wheel
!
! ****** Markers for current part ******
!
marker create  &
   marker_name = .CFR22 Try 3_RT.whr_rear_wheel.cm  &
   location = 0.0, 0.0, 0.0  &
   orientation = 0.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .CFR22 Try 3_RT.whr_rear_wheel.cm  &
   visibility = off  &
   name_visibility = off
!
marker create  &
   marker_name = .CFR22 Try 3_RT.whr_rear_wheel.tire_i  &
   location = 0.0, 0.0, 0.0  &
   orientation = 0.0d, 90.0d, 0.0d
!
marker attributes  &
   marker_name = .CFR22 Try 3_RT.whr_rear_wheel.tire_i  &
   visibility = off  &
   name_visibility = off
!
part create rigid_body mass_properties  &
   part_name = .CFR22 Try 3_RT.whr_rear_wheel  &
   mass = 1.0  &
   center_of_mass_marker = .CFR22 Try 3_RT.whr_rear_wheel.cm  &
   ixx = 1.0  &
   iyy = 1.0  &
   izz = 1.0  &
   ixy = 0.0  &
   izx = 0.0  &
   iyz = 0.0
!
part attributes  &
   part_name = .CFR22 Try 3_RT.whr_rear_wheel  &
   visibility = on  &
   name_visibility = on
!
!----------------------------- Analysis settings ------------------------------!
!
!
!---------------------------- Adams/View Variables ----------------------------!
!
!
variable create  &
   variable_name = .CFR22 Try 3_RT.cil_front_wheel_center  &
   units = "length"  &
   real_value = 0.0, 760.0, 329.0
!
variable create  &
   variable_name = .CFR22 Try 3_RT.cir_front_wheel_center  &
   units = "length"  &
   real_value = 0.0, -760.0, 329.0
!
variable create  &
   variable_name = .CFR22 Try 3_RT.cil_rear_wheel_center  &
   units = "length"  &
   real_value = -2777.2, 797.0, 379.28
!
variable create  &
   variable_name = .CFR22 Try 3_RT.cir_rear_wheel_center  &
   units = "length"  &
   real_value = -2777.2, -797.0, 379.28
!
variable create  &
   variable_name = .CFR22 Try 3_RT.cil_front_toe_angle  &
   units = "no_units"  &
   real_value = 0.0
!
variable create  &
   variable_name = .CFR22 Try 3_RT.cir_front_toe_angle  &
   units = "no_units"  &
   real_value = 0.0
!
variable create  &
   variable_name = .CFR22 Try 3_RT.cil_front_camber_angle  &
   units = "no_units"  &
   real_value = 0.0
!
variable create  &
   variable_name = .CFR22 Try 3_RT.cir_front_camber_angle  &
   units = "no_units"  &
   real_value = 0.0
!
variable create  &
   variable_name = .CFR22 Try 3_RT.cil_rear_camber_angle  &
   units = "no_units"  &
   real_value = 0.0
!
variable create  &
   variable_name = .CFR22 Try 3_RT.cir_rear_camber_angle  &
   units = "no_units"  &
   real_value = 0.0
!
variable create  &
   variable_name = .CFR22 Try 3_RT.cil_rear_toe_angle  &
   units = "no_units"  &
   real_value = 0.0
!
variable create  &
   variable_name = .CFR22 Try 3_RT.cir_rear_toe_angle  &
   units = "no_units"  &
   real_value = 0.0
!
!--------------------------- Expression definitions ---------------------------!
!
!
defaults coordinate_system  &
   default_coordinate_system = ground
!
material modify  &
   material_name = .CFR22 Try 3_RT.steel  &
   youngs_modulus = (2.07E+011(Newton/meter**2))  &
   density = (7801.0(kg/meter**3))
!
marker modify  &
   marker_name = .CFR22 Try 3_RT.ges_chassis.inertia_frame  &
   location =   &
      (LOC_RELATIVE_TO({0, 0, 0}, .CFR22 Try 3_RT.ges_chassis.cm))  &
   orientation =   &
      (ORI_RELATIVE_TO({0, 0, 0}, .CFR22 Try 3_RT.ges_chassis))  &
   relative_to = .CFR22 Try 3_RT.ges_chassis
!
defaults coordinate_system  &
   default_coordinate_system = .CFR22 Try 3_RT.ground
!
marker modify  &
   marker_name = .CFR22 Try 3_RT.ges_chassis.fwl  &
   location =   &
      (.CFR22 Try 3_RT.cil_front_wheel_center)  &
   orientation =   &
      (ORI_RELATIVE_TO({180d - .CFR22 Try 3_RT.cil_front_toe_angle, -90d - .CFR22 Try 3_RT.cil_front_camber_angle, 180d}, .CFR22 Try 3_RT.ground.origo))  &
   relative_to = .CFR22 Try 3_RT.ges_chassis
!
defaults coordinate_system  &
   default_coordinate_system = .CFR22 Try 3_RT.ground
!
marker modify  &
   marker_name = .CFR22 Try 3_RT.ges_chassis.rwl  &
   location =   &
      (.CFR22 Try 3_RT.cil_rear_wheel_center)  &
   orientation =   &
      (ORI_RELATIVE_TO({180d - .CFR22 Try 3_RT.cil_rear_toe_angle, -90d - .CFR22 Try 3_RT.cil_rear_camber_angle, 180d}, .CFR22 Try 3_RT.ground.origo))  &
   relative_to = .CFR22 Try 3_RT.ges_chassis
!
defaults coordinate_system  &
   default_coordinate_system = .CFR22 Try 3_RT.ground
!
marker modify  &
   marker_name = .CFR22 Try 3_RT.ges_chassis.rwr  &
   location =   &
      (.CFR22 Try 3_RT.cir_rear_wheel_center)  &
   orientation =   &
      (ORI_RELATIVE_TO({180d - .CFR22 Try 3_RT.cir_rear_toe_angle, -90d - .CFR22 Try 3_RT.cir_rear_camber_angle, 180d}, .CFR22 Try 3_RT.ground.origo))  &
   relative_to = .CFR22 Try 3_RT.ges_chassis
!
defaults coordinate_system  &
   default_coordinate_system = .CFR22 Try 3_RT.ground
!
marker modify  &
   marker_name = .CFR22 Try 3_RT.ges_chassis.fwr  &
   location =   &
      (.CFR22 Try 3_RT.cir_front_wheel_center)  &
   orientation =   &
      (ORI_RELATIVE_TO({180d - .CFR22 Try 3_RT.cir_front_toe_angle, -90d - .CFR22 Try 3_RT.cir_front_camber_angle, 180d}, .CFR22 Try 3_RT.ground.origo))  &
   relative_to = .CFR22 Try 3_RT.ges_chassis
!
defaults coordinate_system  &
   default_coordinate_system = .CFR22 Try 3_RT.ground
!
marker modify  &
   marker_name = .CFR22 Try 3_RT.whl_front_wheel.tire_i  &
   location =   &
      (LOC_RELATIVE_TO({0, 0, 0}, .CFR22 Try 3_RT.ges_chassis.fwl))  &
   orientation =   &
      (ORI_RELATIVE_TO({0, 0, 0}, .CFR22 Try 3_RT.ges_chassis.fwl))  &
   relative_to = .CFR22 Try 3_RT.whl_front_wheel
!
defaults coordinate_system  &
   default_coordinate_system = .CFR22 Try 3_RT.ground
!
part modify rigid_body name_and_position  &
   part_name = .CFR22 Try 3_RT.whl_front_wheel  &
   location =   &
      (LOC_RELATIVE_TO({0, 0, 0}, .CFR22 Try 3_RT.ges_chassis.fwl))
!
marker modify  &
   marker_name = .CFR22 Try 3_RT.whr_front_wheel.tire_i  &
   location =   &
      (LOC_RELATIVE_TO({0, 0, 0}, .CFR22 Try 3_RT.ges_chassis.fwr))  &
   orientation =   &
      (ORI_RELATIVE_TO({0, 0, 0}, .CFR22 Try 3_RT.ges_chassis.fwr))  &
   relative_to = .CFR22 Try 3_RT.whr_front_wheel
!
defaults coordinate_system  &
   default_coordinate_system = .CFR22 Try 3_RT.ground
!
part modify rigid_body name_and_position  &
   part_name = .CFR22 Try 3_RT.whr_front_wheel  &
   location =   &
      (LOC_RELATIVE_TO({0, 0, 0}, .CFR22 Try 3_RT.ges_chassis.fwr))
!
marker modify  &
   marker_name = .CFR22 Try 3_RT.whl_rear_wheel.tire_i  &
   location =   &
      (LOC_RELATIVE_TO({0, 0, 0}, .CFR22 Try 3_RT.ges_chassis.rwl))  &
   orientation =   &
      (ORI_RELATIVE_TO({0, 0, 0}, .CFR22 Try 3_RT.ges_chassis.rwl))  &
   relative_to = .CFR22 Try 3_RT.whl_rear_wheel
!
defaults coordinate_system  &
   default_coordinate_system = .CFR22 Try 3_RT.ground
!
part modify rigid_body name_and_position  &
   part_name = .CFR22 Try 3_RT.whl_rear_wheel  &
   location =   &
      (LOC_RELATIVE_TO({0, 0, 0}, .CFR22 Try 3_RT.ges_chassis.rwl))
!
marker modify  &
   marker_name = .CFR22 Try 3_RT.whr_rear_wheel.tire_i  &
   location =   &
      (LOC_RELATIVE_TO({0, 0, 0}, .CFR22 Try 3_RT.ges_chassis.rwr))  &
   orientation =   &
      (ORI_RELATIVE_TO({0, 0, 0}, .CFR22 Try 3_RT.ges_chassis.rwr))  &
   relative_to = .CFR22 Try 3_RT.whr_rear_wheel
!
defaults coordinate_system  &
   default_coordinate_system = .CFR22 Try 3_RT.ground
!
part modify rigid_body name_and_position  &
   part_name = .CFR22 Try 3_RT.whr_rear_wheel  &
   location =   &
      (LOC_RELATIVE_TO({0, 0, 0}, .CFR22 Try 3_RT.ges_chassis.rwr))
!
model display  &
   model_name = CFR22 Try 3_RT
!
!---- Customization commands
!
marker create  &
   marker_name = .CFR22 Try 3_RT.ges_chassis.geo_mar  &
   location = 0, 0.0, 0.0  &
   orientation = 0.0d, 0.0d, 0.0d
geometry create shape shell  &
   shell_name = .CFR22 Try 3_RT.ges_chassis.Body  &
   reference_marker = .CFR22 Try 3_RT.ges_chassis.geo_mar  &
   file_name = "mdids://VI_Racer/shell_graphics.tbl/CFR22 Try 3_RT_ges_chassis.shl"  &
   wireframe_only = no
geometry attributes  &
   geometry_name = .CFR22 Try 3_RT.ges_chassis.Body  &
   transparency = 0 &
   color = red
variable set  &
   variable_name = .CFR22 Try 3_RT.cil_front_wheel_center  &
   real_value = 0.0, 862.5, 329.0
variable set  &
   variable_name = .CFR22 Try 3_RT.cir_front_wheel_center  &
   real_value = 0.0, -862.5, 329.0
variable set  &
   variable_name = .CFR22 Try 3_RT.cil_rear_wheel_center  &
   real_value = -1219.0, 862.5, 360.0
variable set  &
   variable_name = .CFR22 Try 3_RT.cir_rear_wheel_center  &
   real_value = -1219.0, -862.5, 360.0
!
defaults model  &
   part_name = .CFR22 Try 3_RT.whl_front_wheel
geometry create shape shell  &
   file_name = "mdids://VI_Racer/shell_graphics.tbl/CFR22 Try 3_RT_whl_front_rim.shl"  &
   shell_name = rim  &
   reference_marker = .CFR22 Try 3_RT.whl_front_wheel.tire_i  &
   wireframe_only = no
geometry create shape shell  &
   file_name = "mdids://VI_Racer/shell_graphics.tbl/CFR22 Try 3_RT_whl_front_tire.shl"  &
   shell_name = tire  &
   reference_marker = .CFR22 Try 3_RT.whl_front_wheel.tire_i  &
   wireframe_only = no
!
defaults model  &
   part_name = .CFR22 Try 3_RT.whr_front_wheel
geometry create shape shell  &
   file_name = "mdids://VI_Racer/shell_graphics.tbl/CFR22 Try 3_RT_whr_front_rim.shl"  &
   shell_name = rim  &
   reference_marker = .CFR22 Try 3_RT.whr_front_wheel.tire_i  &
   wireframe_only = no
geometry create shape shell  &
   file_name = "mdids://VI_Racer/shell_graphics.tbl/CFR22 Try 3_RT_whr_front_tire.shl"  &
   shell_name = tire  &
   reference_marker = .CFR22 Try 3_RT.whr_front_wheel.tire_i  &
   wireframe_only = no
!
defaults model  &
   part_name = .CFR22 Try 3_RT.whl_rear_wheel
geometry create shape shell  &
   file_name = "mdids://VI_Racer/shell_graphics.tbl/CFR22 Try 3_RT_whl_rear_rim.shl"  &
   shell_name = rim  &
   reference_marker = .CFR22 Try 3_RT.whl_rear_wheel.tire_i  &
   wireframe_only = no
geometry create shape shell  &
   file_name = "mdids://VI_Racer/shell_graphics.tbl/CFR22 Try 3_RT_whl_rear_tire.shl"  &
   shell_name = tire  &
   reference_marker = .CFR22 Try 3_RT.whl_rear_wheel.tire_i  &
   wireframe_only = no
!
defaults model  &
   part_name = .CFR22 Try 3_RT.whr_rear_wheel
geometry create shape shell  &
   file_name = "mdids://VI_Racer/shell_graphics.tbl/CFR22 Try 3_RT_whr_rear_rim.shl"  &
   shell_name = rim  &
   reference_marker = .CFR22 Try 3_RT.whr_rear_wheel.tire_i  &
   wireframe_only = no
geometry create shape shell  &
   file_name = "mdids://VI_Racer/shell_graphics.tbl/CFR22 Try 3_RT_whr_rear_tire.shl"  &
   shell_name = tire  &
   reference_marker = .CFR22 Try 3_RT.whr_rear_wheel.tire_i  &
   wireframe_only = no
!
entity attributes &
 entity_name     = whl_front_wheel.rim,whr_front_wheel.rim,whl_rear_wheel.rim,whr_rear_wheel.rim &
 color           = DARK_GRAY 
entity attributes &
 entity_name     = whl_front_wheel.tire,whr_front_wheel.tire,whl_rear_wheel.tire,whr_rear_wheel.tire &
 color           = BLACK 
