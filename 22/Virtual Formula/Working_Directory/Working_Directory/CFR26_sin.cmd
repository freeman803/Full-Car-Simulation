if cond=(eval(db_exists("VI_Racer_RT")))
  return
end
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
   icon_visibility = off  &
   grid_visibility = off  &
   size_of_icons = 50.0  &
   spacing_for_grid = 50.0
!
!------------------------------ Adams/View Model ------------------------------!
!
!
model create  &
   model_name = VI_Racer_RT  &
   title = "ADAMS/Car template"
!
view erase
!
!-------------------------------- Data storage --------------------------------!
!
!
data_element create string  &
   string_name = .VI_Racer_RT.minor_role_string  &
   string = ""
!
!--------------------------------- Materials ----------------------------------!
!
!
material create  &
   material_name = .VI_Racer_RT.steel  &
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
   default_coordinate_system = .VI_Racer_RT.ground
!
! ****** Markers for current part ******
!
marker create  &
   marker_name = .VI_Racer_RT.ground.origo  &
   location = 0.0, 0.0, 0.0  &
   orientation = 0.0d, 0.0d, 0.0d
!
marker create  &
   marker_name = .VI_Racer_RT.ground.shell_Ref  &
   location = 0.0, 0.0, -345.0  &
   orientation = 0.0d, 0.0d, 0.0d
!
!-------------------------------- ges_chassis ---------------------------------!
!
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.ground
!
part create rigid_body name_and_position  &
   part_name = .VI_Racer_RT.ges_chassis  &
   adams_id = 2  &
   location = 0.0, 0.0, 0.0  &
   orientation = 0.0d, 0.0d, 0.0d
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.ges_chassis
!
! ****** Markers for current part ******
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.cm  &
   location = 1500.0, 0.0, 300.0  &
   orientation = 0.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.ges_chassis.cm  &
   visibility = off  &
   name_visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.inertia_frame  &
   location = 1500.0, 0.0, 300.0  &
   orientation = 0.0d, 0.0d, 0.0d
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.fwl  &
   location = 0.0, 700.0, 251.2  &
   orientation = 0.0d, 90.0d, 0.0d
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.rwl  &
   location = -1542.4, 700.0, 250.0  &
   orientation = 0.0d, 90.0d, 0.0d
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.rwr  &
   location = -1542.4, -700.0, 250.0  &
   orientation = 0.0d, 90.0d, 0.0d
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.fwr  &
   location = 0.0, -700.0, 251.2  &
   orientation = 0.0d, 90.0d, 0.0d
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_758  &
   adams_id = 758  &
   location = 81.0, -700.0, 765.33  &
   orientation = 180.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_758  &
   visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_759  &
   adams_id = 759  &
   location = -1135.03, -706.97, 1002.08  &
   orientation = 180.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_759  &
   visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_760  &
   adams_id = 760  &
   location = -1698.9, -579.43, 1378.43  &
   orientation = 180.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_760  &
   visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_766  &
   adams_id = 766  &
   location = -2947.05, -561.2, 1382.49  &
   orientation = 180.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_766  &
   visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_767  &
   adams_id = 767  &
   location = -3578.52, -624.57, 1095.27  &
   orientation = 180.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_767  &
   visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_768  &
   adams_id = 768  &
   location = -4018.18, -599.77, 1085.1  &
   orientation = 180.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_768  &
   visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_769  &
   adams_id = 769  &
   location = -4018.18, 599.77, 1085.1  &
   orientation = 180.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_769  &
   visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_770  &
   adams_id = 770  &
   location = -3578.52, 624.57, 1095.27  &
   orientation = 180.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_770  &
   visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_771  &
   adams_id = 771  &
   location = -2947.05, 561.2, 1382.49  &
   orientation = 180.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_771  &
   visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_772  &
   adams_id = 772  &
   location = -1698.9, 579.43, 1378.43  &
   orientation = 180.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_772  &
   visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_773  &
   adams_id = 773  &
   location = -1135.03, 706.97, 1002.08  &
   orientation = 180.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_773  &
   visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_774  &
   adams_id = 774  &
   location = 81.0, 700.0, 765.33  &
   orientation = 180.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_774  &
   visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_775  &
   adams_id = 775  &
   location = 177.0, -400.0, 355.5  &
   orientation = 180.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_775  &
   visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_776  &
   adams_id = 776  &
   location = 177.0, 400.0, 355.5  &
   orientation = 180.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_776  &
   visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_777  &
   adams_id = 777  &
   location = -962.0, 400.0, 354.0  &
   orientation = 180.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_777  &
   visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_778  &
   adams_id = 778  &
   location = -1329.0, 685.0, 347.0  &
   orientation = 180.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_778  &
   visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_779  &
   adams_id = 779  &
   location = -2075.78, 685.0, 343.0  &
   orientation = 180.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_779  &
   visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_780  &
   adams_id = 780  &
   location = -2444.27, 685.0, 454.5  &
   orientation = 180.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_780  &
   visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_781  &
   adams_id = 781  &
   location = -2923.09, 620.85, 530.37  &
   orientation = 180.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_781  &
   visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_782  &
   adams_id = 782  &
   location = -4032.11, 627.0, 601.0  &
   orientation = 180.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_782  &
   visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_783  &
   adams_id = 783  &
   location = -4032.11, -627.0, 601.0  &
   orientation = 180.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_783  &
   visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_784  &
   adams_id = 784  &
   location = -2923.09, -620.85, 530.37  &
   orientation = 180.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_784  &
   visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_785  &
   adams_id = 785  &
   location = -2444.27, -685.0, 454.5  &
   orientation = 180.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_785  &
   visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_786  &
   adams_id = 786  &
   location = -2075.78, -685.0, 343.0  &
   orientation = 180.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_786  &
   visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_787  &
   adams_id = 787  &
   location = -1329.0, -685.0, 347.0  &
   orientation = 180.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_787  &
   visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_788  &
   adams_id = 788  &
   location = -962.0, -400.0, 354.0  &
   orientation = 180.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.ges_chassis.MARKER_788  &
   visibility = off
!
part create rigid_body mass_properties  &
   part_name = .VI_Racer_RT.ges_chassis  &
   mass = 1.0  &
   center_of_mass_marker = .VI_Racer_RT.ges_chassis.cm  &
   inertia_marker = .VI_Racer_RT.ges_chassis.inertia_frame  &
   ixx = 1.0  &
   iyy = 1.0  &
   izz = 1.0  &
   ixy = 0.0  &
   izx = 0.0  &
   iyz = 0.0
!
! ****** Graphics for current part ******
!
geometry create curve outline  &
   outline_name = .VI_Racer_RT.ges_chassis.r_body  &
   adams_id = 220  &
   marker_name =  &
      .VI_Racer_RT.ges_chassis.MARKER_758,  &
      .VI_Racer_RT.ges_chassis.MARKER_759,  &
      .VI_Racer_RT.ges_chassis.MARKER_760,  &
      .VI_Racer_RT.ges_chassis.MARKER_766,  &
      .VI_Racer_RT.ges_chassis.MARKER_767,  &
      .VI_Racer_RT.ges_chassis.MARKER_768,  &
      .VI_Racer_RT.ges_chassis.MARKER_769,  &
      .VI_Racer_RT.ges_chassis.MARKER_770,  &
      .VI_Racer_RT.ges_chassis.MARKER_771,  &
      .VI_Racer_RT.ges_chassis.MARKER_772,  &
      .VI_Racer_RT.ges_chassis.MARKER_773,  &
      .VI_Racer_RT.ges_chassis.MARKER_774,  &
      .VI_Racer_RT.ges_chassis.MARKER_758,  &
      .VI_Racer_RT.ges_chassis.MARKER_775,  &
      .VI_Racer_RT.ges_chassis.MARKER_776,  &
      .VI_Racer_RT.ges_chassis.MARKER_777,  &
      .VI_Racer_RT.ges_chassis.MARKER_778,  &
      .VI_Racer_RT.ges_chassis.MARKER_779,  &
      .VI_Racer_RT.ges_chassis.MARKER_780,  &
      .VI_Racer_RT.ges_chassis.MARKER_781,  &
      .VI_Racer_RT.ges_chassis.MARKER_782,  &
      .VI_Racer_RT.ges_chassis.MARKER_769,  &
      .VI_Racer_RT.ges_chassis.MARKER_782,  &
      .VI_Racer_RT.ges_chassis.MARKER_783,  &
      .VI_Racer_RT.ges_chassis.MARKER_768,  &
      .VI_Racer_RT.ges_chassis.MARKER_783,  &
      .VI_Racer_RT.ges_chassis.MARKER_784,  &
      .VI_Racer_RT.ges_chassis.MARKER_785,  &
      .VI_Racer_RT.ges_chassis.MARKER_786,  &
      .VI_Racer_RT.ges_chassis.MARKER_787,  &
      .VI_Racer_RT.ges_chassis.MARKER_788,  &
      .VI_Racer_RT.ges_chassis.MARKER_775,  &
      .VI_Racer_RT.ges_chassis.MARKER_776,  &
      .VI_Racer_RT.ges_chassis.MARKER_774,  &
      .VI_Racer_RT.ges_chassis.MARKER_773,  &
      .VI_Racer_RT.ges_chassis.MARKER_759,  &
      .VI_Racer_RT.ges_chassis.MARKER_760,  &
      .VI_Racer_RT.ges_chassis.MARKER_772,  &
      .VI_Racer_RT.ges_chassis.MARKER_771,  &
      .VI_Racer_RT.ges_chassis.MARKER_766,  &
      .VI_Racer_RT.ges_chassis.MARKER_767,  &
      .VI_Racer_RT.ges_chassis.MARKER_770  &
   visibility_between_markers = on, on, on, on, on, on, on, on, on, on, on,  &
                                on, on, on, on, on, on, on, on, on, on, on,  &
                                on, on, on, on, on, on, on, on, on, on, on,  &
                                on, on, on, on, on, on, on, on, on  &
   close = no
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.ges_chassis.r_body  &
   active = on  &
   visibility = off
!
part attributes  &
   part_name = .VI_Racer_RT.ges_chassis  &
   visibility = on  &
   name_visibility = on
!
!--------------------------------- ges_engine ---------------------------------!
!
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.ground
!
part create rigid_body name_and_position  &
   part_name = .VI_Racer_RT.ges_engine  &
   adams_id = 7  &
   location = 0.0, 0.0, 0.0  &
   orientation = 0.0d, 0.0d, 0.0d
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.ges_engine
!
! ****** Markers for current part ******
!
marker create  &
   marker_name = .VI_Racer_RT.ges_engine.cm  &
   location = 1500.0, 0.0, 300.0  &
   orientation = 0.0d, 0.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.ges_engine.cm  &
   visibility = off  &
   name_visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.ges_engine.inertia_frame  &
   location = 1500.0, 0.0, 300.0  &
   orientation = 0.0d, 0.0d, 0.0d
!
part create rigid_body mass_properties  &
   part_name = .VI_Racer_RT.ges_engine  &
   mass = 1.0  &
   center_of_mass_marker = .VI_Racer_RT.ges_engine.cm  &
   inertia_marker = .VI_Racer_RT.ges_engine.inertia_frame  &
   ixx = 1.0  &
   iyy = 1.0  &
   izz = 1.0  &
   ixy = 0.0  &
   izx = 0.0  &
   iyz = 0.0
!
part attributes  &
   part_name = .VI_Racer_RT.ges_engine  &
   visibility = on  &
   name_visibility = on
!
!------------------------------ whl_front_wheel -------------------------------!
!
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.ground
!
part create rigid_body name_and_position  &
   part_name = .VI_Racer_RT.whl_front_wheel  &
   adams_id = 3  &
   location = 0.0, 700.0, 251.2  &
   orientation = 0.0d, 0.0d, 0.0d
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.whl_front_wheel
!
! ****** Markers for current part ******
!
marker create  &
   marker_name = .VI_Racer_RT.whl_front_wheel.cm  &
   location = 0.0, 0.0, 0.0  &
   orientation = 0.0d, 0.0d, 0.0d
!
marker create  &
   marker_name = .VI_Racer_RT.whl_front_wheel.tire_i  &
   location = 0.0, 0.0, 0.0  &
   orientation = 0.0d, 90.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.whl_front_wheel.tire_i  &
   visibility = off  &
   name_visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.whl_front_wheel.geo_ctr  &
   location = 0.0, 20.0, 0.0  &
   orientation = 0.0d, 90.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.whl_front_wheel.geo_ctr  &
   visibility = off  &
   name_visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.whl_front_wheel.geo_inr  &
   location = 0.0, 100.0, 0.0  &
   orientation = 180.0d, 90.0d, 180.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.whl_front_wheel.geo_inr  &
   visibility = off  &
   name_visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.whl_front_wheel.geo_otr  &
   location = 0.0, -100.0, 0.0  &
   orientation = 0.0d, 90.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.whl_front_wheel.geo_otr  &
   visibility = off  &
   name_visibility = off
!
part create rigid_body mass_properties  &
   part_name = .VI_Racer_RT.whl_front_wheel  &
   mass = 1.0  &
   center_of_mass_marker = .VI_Racer_RT.whl_front_wheel.cm  &
   ixx = 1.0  &
   iyy = 1.0  &
   izz = 1.0  &
   ixy = 0.0  &
   izx = 0.0  &
   iyz = 0.0
!
! ****** Graphics for current part ******
!
geometry create shape cylinder  &
   cylinder_name = .VI_Racer_RT.whl_front_wheel.wheel_hub  &
   center_marker = .VI_Racer_RT.whl_front_wheel.geo_ctr  &
   angle_extent = 360.0  &
   length = 40.0  &
   radius = 145.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 20
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whl_front_wheel.wheel_hub  &
   color = SILVER
!
geometry create shape cylinder  &
   cylinder_name = .VI_Racer_RT.whl_front_wheel.wheel_rim  &
   center_marker = .VI_Racer_RT.whl_front_wheel.geo_inr  &
   angle_extent = 360.0  &
   length = -200.0  &
   radius = 145.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whl_front_wheel.wheel_rim  &
   color = SILVER
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whl_front_wheel.wheel_inner1  &
   center_marker = .VI_Racer_RT.whl_front_wheel.geo_inr  &
   angle_extent = 360.0  &
   length = 0.0  &
   top_radius = 145.0  &
   bottom_radius = 170.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whl_front_wheel.wheel_inner1  &
   color = SILVER
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whl_front_wheel.wheel_outer1  &
   center_marker = .VI_Racer_RT.whl_front_wheel.geo_otr  &
   angle_extent = 360.0  &
   length = 0.0  &
   top_radius = 145.0  &
   bottom_radius = 170.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whl_front_wheel.wheel_outer1  &
   color = SILVER
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whl_front_wheel.wheel_mark_outer  &
   center_marker = .VI_Racer_RT.whl_front_wheel.geo_otr  &
   angle_extent = 20.0  &
   length = 2.0  &
   top_radius = 0.0  &
   bottom_radius = 170.0  &
   side_count_for_body = 1  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whl_front_wheel.wheel_mark_outer  &
   color = RED
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whl_front_wheel.wheel_mark_inner  &
   center_marker = .VI_Racer_RT.whl_front_wheel.geo_inr  &
   angle_extent = -20.0  &
   length = -2.0  &
   top_radius = 0.0  &
   bottom_radius = 170.0  &
   side_count_for_body = 1  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whl_front_wheel.wheel_mark_inner  &
   color = RED
!
geometry create shape cylinder  &
   cylinder_name = .VI_Racer_RT.whl_front_wheel.tire_tread  &
   center_marker = .VI_Racer_RT.whl_front_wheel.geo_inr  &
   angle_extent = 360.0  &
   length = -200.0  &
   radius = 250.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whl_front_wheel.tire_tread  &
   color = DARK_GRAY
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whl_front_wheel.tire_sidewall1  &
   center_marker = .VI_Racer_RT.whl_front_wheel.geo_inr  &
   angle_extent = 360.0  &
   length = 20.0  &
   top_radius = 210.0  &
   bottom_radius = 170.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whl_front_wheel.tire_sidewall1  &
   color = DARK_GRAY
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whl_front_wheel.tire_sidewall2  &
   center_marker = .VI_Racer_RT.whl_front_wheel.geo_inr  &
   angle_extent = 360.0  &
   length = 20.0  &
   top_radius = 210.0  &
   bottom_radius = 250.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whl_front_wheel.tire_sidewall2  &
   color = DARK_GRAY
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whl_front_wheel.tire_sidewall3  &
   center_marker = .VI_Racer_RT.whl_front_wheel.geo_otr  &
   angle_extent = 360.0  &
   length = 20.0  &
   top_radius = 210.0  &
   bottom_radius = 170.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whl_front_wheel.tire_sidewall3  &
   color = DARK_GRAY
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whl_front_wheel.tire_sidewall4  &
   center_marker = .VI_Racer_RT.whl_front_wheel.geo_otr  &
   angle_extent = 360.0  &
   length = 20.0  &
   top_radius = 210.0  &
   bottom_radius = 250.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whl_front_wheel.tire_sidewall4  &
   color = DARK_GRAY
!
part attributes  &
   part_name = .VI_Racer_RT.whl_front_wheel  &
   visibility = on  &
   name_visibility = on
!
!------------------------------ whr_front_wheel -------------------------------!
!
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.ground
!
part create rigid_body name_and_position  &
   part_name = .VI_Racer_RT.whr_front_wheel  &
   adams_id = 5  &
   location = 0.0, -700.0, 251.2  &
   orientation = 0.0d, 0.0d, 0.0d
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.whr_front_wheel
!
! ****** Markers for current part ******
!
marker create  &
   marker_name = .VI_Racer_RT.whr_front_wheel.cm  &
   location = 0.0, 0.0, 0.0  &
   orientation = 0.0d, 0.0d, 0.0d
!
marker create  &
   marker_name = .VI_Racer_RT.whr_front_wheel.tire_i  &
   location = 0.0, 0.0, 0.0  &
   orientation = 0.0d, 90.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.whr_front_wheel.tire_i  &
   visibility = off  &
   name_visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.whr_front_wheel.geo_ctr  &
   location = 0.0, 20.0, 0.0  &
   orientation = 0.0d, 90.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.whr_front_wheel.geo_ctr  &
   visibility = off  &
   name_visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.whr_front_wheel.geo_inr  &
   location = 0.0, 100.0, 0.0  &
   orientation = 180.0d, 90.0d, 180.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.whr_front_wheel.geo_inr  &
   visibility = off  &
   name_visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.whr_front_wheel.geo_otr  &
   location = 0.0, -100.0, 0.0  &
   orientation = 0.0d, 90.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.whr_front_wheel.geo_otr  &
   visibility = off  &
   name_visibility = off
!
part create rigid_body mass_properties  &
   part_name = .VI_Racer_RT.whr_front_wheel  &
   mass = 1.0  &
   center_of_mass_marker = .VI_Racer_RT.whr_front_wheel.cm  &
   ixx = 1.0  &
   iyy = 1.0  &
   izz = 1.0  &
   ixy = 0.0  &
   izx = 0.0  &
   iyz = 0.0
!
! ****** Graphics for current part ******
!
geometry create shape cylinder  &
   cylinder_name = .VI_Racer_RT.whr_front_wheel.wheel_hub  &
   center_marker = .VI_Racer_RT.whr_front_wheel.geo_ctr  &
   angle_extent = 360.0  &
   length = 40.0  &
   radius = 145.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 20
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whr_front_wheel.wheel_hub  &
   color = SILVER
!
geometry create shape cylinder  &
   cylinder_name = .VI_Racer_RT.whr_front_wheel.wheel_rim  &
   center_marker = .VI_Racer_RT.whr_front_wheel.geo_inr  &
   angle_extent = 360.0  &
   length = -200.0  &
   radius = 145.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whr_front_wheel.wheel_rim  &
   color = SILVER
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whr_front_wheel.wheel_inner1  &
   center_marker = .VI_Racer_RT.whr_front_wheel.geo_inr  &
   angle_extent = 360.0  &
   length = 0.0  &
   top_radius = 145.0  &
   bottom_radius = 170.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whr_front_wheel.wheel_inner1  &
   color = SILVER
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whr_front_wheel.wheel_outer1  &
   center_marker = .VI_Racer_RT.whr_front_wheel.geo_otr  &
   angle_extent = 360.0  &
   length = 0.0  &
   top_radius = 145.0  &
   bottom_radius = 170.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whr_front_wheel.wheel_outer1  &
   color = SILVER
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whr_front_wheel.wheel_mark_outer  &
   center_marker = .VI_Racer_RT.whr_front_wheel.geo_otr  &
   angle_extent = 20.0  &
   length = 2.0  &
   top_radius = 0.0  &
   bottom_radius = 170.0  &
   side_count_for_body = 1  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whr_front_wheel.wheel_mark_outer  &
   color = RED
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whr_front_wheel.wheel_mark_inner  &
   center_marker = .VI_Racer_RT.whr_front_wheel.geo_inr  &
   angle_extent = -20.0  &
   length = -2.0  &
   top_radius = 0.0  &
   bottom_radius = 170.0  &
   side_count_for_body = 1  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whr_front_wheel.wheel_mark_inner  &
   color = RED
!
geometry create shape cylinder  &
   cylinder_name = .VI_Racer_RT.whr_front_wheel.tire_tread  &
   center_marker = .VI_Racer_RT.whr_front_wheel.geo_inr  &
   angle_extent = 360.0  &
   length = -200.0  &
   radius = 250.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whr_front_wheel.tire_tread  &
   color = DARK_GRAY
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whr_front_wheel.tire_sidewall1  &
   center_marker = .VI_Racer_RT.whr_front_wheel.geo_inr  &
   angle_extent = 360.0  &
   length = 20.0  &
   top_radius = 210.0  &
   bottom_radius = 170.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whr_front_wheel.tire_sidewall1  &
   color = DARK_GRAY
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whr_front_wheel.tire_sidewall2  &
   center_marker = .VI_Racer_RT.whr_front_wheel.geo_inr  &
   angle_extent = 360.0  &
   length = 20.0  &
   top_radius = 210.0  &
   bottom_radius = 250.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whr_front_wheel.tire_sidewall2  &
   color = DARK_GRAY
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whr_front_wheel.tire_sidewall3  &
   center_marker = .VI_Racer_RT.whr_front_wheel.geo_otr  &
   angle_extent = 360.0  &
   length = 20.0  &
   top_radius = 210.0  &
   bottom_radius = 170.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whr_front_wheel.tire_sidewall3  &
   color = DARK_GRAY
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whr_front_wheel.tire_sidewall4  &
   center_marker = .VI_Racer_RT.whr_front_wheel.geo_otr  &
   angle_extent = 360.0  &
   length = 20.0  &
   top_radius = 210.0  &
   bottom_radius = 250.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whr_front_wheel.tire_sidewall4  &
   color = DARK_GRAY
!
part attributes  &
   part_name = .VI_Racer_RT.whr_front_wheel  &
   visibility = on  &
   name_visibility = on
!
!------------------------------- whl_rear_wheel -------------------------------!
!
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.ground
!
part create rigid_body name_and_position  &
   part_name = .VI_Racer_RT.whl_rear_wheel  &
   adams_id = 4  &
   location = -1542.4, 700.0, 250.0  &
   orientation = 0.0d, 0.0d, 0.0d
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.whl_rear_wheel
!
! ****** Markers for current part ******
!
marker create  &
   marker_name = .VI_Racer_RT.whl_rear_wheel.cm  &
   location = 0.0, 0.0, 0.0  &
   orientation = 0.0d, 0.0d, 0.0d
!
marker create  &
   marker_name = .VI_Racer_RT.whl_rear_wheel.tire_i  &
   location = 0.0, 0.0, 0.0  &
   orientation = 0.0d, 90.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.whl_rear_wheel.tire_i  &
   visibility = off  &
   name_visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.whl_rear_wheel.geo_ctr  &
   location = 0.0, 20.0, 0.0  &
   orientation = 0.0d, 90.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.whl_rear_wheel.geo_ctr  &
   visibility = off  &
   name_visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.whl_rear_wheel.geo_inr  &
   location = 0.0, 100.0, 0.0  &
   orientation = 180.0d, 90.0d, 180.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.whl_rear_wheel.geo_inr  &
   visibility = off  &
   name_visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.whl_rear_wheel.geo_otr  &
   location = 0.0, -100.0, 0.0  &
   orientation = 0.0d, 90.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.whl_rear_wheel.geo_otr  &
   visibility = off  &
   name_visibility = off
!
part create rigid_body mass_properties  &
   part_name = .VI_Racer_RT.whl_rear_wheel  &
   mass = 1.0  &
   center_of_mass_marker = .VI_Racer_RT.whl_rear_wheel.cm  &
   ixx = 1.0  &
   iyy = 1.0  &
   izz = 1.0  &
   ixy = 0.0  &
   izx = 0.0  &
   iyz = 0.0
!
! ****** Graphics for current part ******
!
geometry create shape cylinder  &
   cylinder_name = .VI_Racer_RT.whl_rear_wheel.wheel_hub  &
   center_marker = .VI_Racer_RT.whl_rear_wheel.geo_ctr  &
   angle_extent = 360.0  &
   length = 40.0  &
   radius = 145.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 20
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whl_rear_wheel.wheel_hub  &
   color = SILVER
!
geometry create shape cylinder  &
   cylinder_name = .VI_Racer_RT.whl_rear_wheel.wheel_rim  &
   center_marker = .VI_Racer_RT.whl_rear_wheel.geo_inr  &
   angle_extent = 360.0  &
   length = -200.0  &
   radius = 145.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whl_rear_wheel.wheel_rim  &
   color = SILVER
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whl_rear_wheel.wheel_inner1  &
   center_marker = .VI_Racer_RT.whl_rear_wheel.geo_inr  &
   angle_extent = 360.0  &
   length = 0.0  &
   top_radius = 145.0  &
   bottom_radius = 170.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whl_rear_wheel.wheel_inner1  &
   color = SILVER
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whl_rear_wheel.wheel_outer1  &
   center_marker = .VI_Racer_RT.whl_rear_wheel.geo_otr  &
   angle_extent = 360.0  &
   length = 0.0  &
   top_radius = 145.0  &
   bottom_radius = 170.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whl_rear_wheel.wheel_outer1  &
   color = SILVER
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whl_rear_wheel.wheel_mark_outer  &
   center_marker = .VI_Racer_RT.whl_rear_wheel.geo_otr  &
   angle_extent = 20.0  &
   length = 2.0  &
   top_radius = 0.0  &
   bottom_radius = 170.0  &
   side_count_for_body = 1  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whl_rear_wheel.wheel_mark_outer  &
   color = RED
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whl_rear_wheel.wheel_mark_inner  &
   center_marker = .VI_Racer_RT.whl_rear_wheel.geo_inr  &
   angle_extent = -20.0  &
   length = -2.0  &
   top_radius = 0.0  &
   bottom_radius = 170.0  &
   side_count_for_body = 1  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whl_rear_wheel.wheel_mark_inner  &
   color = RED
!
geometry create shape cylinder  &
   cylinder_name = .VI_Racer_RT.whl_rear_wheel.tire_tread  &
   center_marker = .VI_Racer_RT.whl_rear_wheel.geo_inr  &
   angle_extent = 360.0  &
   length = -200.0  &
   radius = 250.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whl_rear_wheel.tire_tread  &
   color = DARK_GRAY
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whl_rear_wheel.tire_sidewall1  &
   center_marker = .VI_Racer_RT.whl_rear_wheel.geo_inr  &
   angle_extent = 360.0  &
   length = 20.0  &
   top_radius = 210.0  &
   bottom_radius = 170.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whl_rear_wheel.tire_sidewall1  &
   color = DARK_GRAY
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whl_rear_wheel.tire_sidewall2  &
   center_marker = .VI_Racer_RT.whl_rear_wheel.geo_inr  &
   angle_extent = 360.0  &
   length = 20.0  &
   top_radius = 210.0  &
   bottom_radius = 250.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whl_rear_wheel.tire_sidewall2  &
   color = DARK_GRAY
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whl_rear_wheel.tire_sidewall3  &
   center_marker = .VI_Racer_RT.whl_rear_wheel.geo_otr  &
   angle_extent = 360.0  &
   length = 20.0  &
   top_radius = 210.0  &
   bottom_radius = 170.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whl_rear_wheel.tire_sidewall3  &
   color = DARK_GRAY
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whl_rear_wheel.tire_sidewall4  &
   center_marker = .VI_Racer_RT.whl_rear_wheel.geo_otr  &
   angle_extent = 360.0  &
   length = 20.0  &
   top_radius = 210.0  &
   bottom_radius = 250.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whl_rear_wheel.tire_sidewall4  &
   color = DARK_GRAY
!
part attributes  &
   part_name = .VI_Racer_RT.whl_rear_wheel  &
   visibility = on  &
   name_visibility = on
!
!------------------------------- whr_rear_wheel -------------------------------!
!
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.ground
!
part create rigid_body name_and_position  &
   part_name = .VI_Racer_RT.whr_rear_wheel  &
   adams_id = 6  &
   location = -1542.4, -700.0, 250.0  &
   orientation = 0.0d, 0.0d, 0.0d
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.whr_rear_wheel
!
! ****** Markers for current part ******
!
marker create  &
   marker_name = .VI_Racer_RT.whr_rear_wheel.cm  &
   location = 0.0, 0.0, 0.0  &
   orientation = 0.0d, 0.0d, 0.0d
!
marker create  &
   marker_name = .VI_Racer_RT.whr_rear_wheel.tire_i  &
   location = 0.0, 0.0, 0.0  &
   orientation = 0.0d, 90.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.whr_rear_wheel.tire_i  &
   visibility = off  &
   name_visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.whr_rear_wheel.geo_ctr  &
   location = 0.0, 20.0, 0.0  &
   orientation = 0.0d, 90.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.whr_rear_wheel.geo_ctr  &
   visibility = off  &
   name_visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.whr_rear_wheel.geo_inr  &
   location = 0.0, 100.0, 0.0  &
   orientation = 180.0d, 90.0d, 180.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.whr_rear_wheel.geo_inr  &
   visibility = off  &
   name_visibility = off
!
marker create  &
   marker_name = .VI_Racer_RT.whr_rear_wheel.geo_otr  &
   location = 0.0, -100.0, 0.0  &
   orientation = 0.0d, 90.0d, 0.0d
!
marker attributes  &
   marker_name = .VI_Racer_RT.whr_rear_wheel.geo_otr  &
   visibility = off  &
   name_visibility = off
!
part create rigid_body mass_properties  &
   part_name = .VI_Racer_RT.whr_rear_wheel  &
   mass = 1.0  &
   center_of_mass_marker = .VI_Racer_RT.whr_rear_wheel.cm  &
   ixx = 1.0  &
   iyy = 1.0  &
   izz = 1.0  &
   ixy = 0.0  &
   izx = 0.0  &
   iyz = 0.0
!
! ****** Graphics for current part ******
!
geometry create shape cylinder  &
   cylinder_name = .VI_Racer_RT.whr_rear_wheel.wheel_hub  &
   center_marker = .VI_Racer_RT.whr_rear_wheel.geo_ctr  &
   angle_extent = 360.0  &
   length = 40.0  &
   radius = 145.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 20
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whr_rear_wheel.wheel_hub  &
   color = SILVER
!
geometry create shape cylinder  &
   cylinder_name = .VI_Racer_RT.whr_rear_wheel.wheel_rim  &
   center_marker = .VI_Racer_RT.whr_rear_wheel.geo_inr  &
   angle_extent = 360.0  &
   length = -200.0  &
   radius = 145.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whr_rear_wheel.wheel_rim  &
   color = SILVER
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whr_rear_wheel.wheel_inner1  &
   center_marker = .VI_Racer_RT.whr_rear_wheel.geo_inr  &
   angle_extent = 360.0  &
   length = 0.0  &
   top_radius = 145.0  &
   bottom_radius = 170.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whr_rear_wheel.wheel_inner1  &
   color = SILVER
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whr_rear_wheel.wheel_outer1  &
   center_marker = .VI_Racer_RT.whr_rear_wheel.geo_otr  &
   angle_extent = 360.0  &
   length = 0.0  &
   top_radius = 145.0  &
   bottom_radius = 170.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whr_rear_wheel.wheel_outer1  &
   color = SILVER
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whr_rear_wheel.wheel_mark_outer  &
   center_marker = .VI_Racer_RT.whr_rear_wheel.geo_otr  &
   angle_extent = 20.0  &
   length = 2.0  &
   top_radius = 0.0  &
   bottom_radius = 170.0  &
   side_count_for_body = 1  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whr_rear_wheel.wheel_mark_outer  &
   color = RED
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whr_rear_wheel.wheel_mark_inner  &
   center_marker = .VI_Racer_RT.whr_rear_wheel.geo_inr  &
   angle_extent = -20.0  &
   length = -2.0  &
   top_radius = 0.0  &
   bottom_radius = 170.0  &
   side_count_for_body = 1  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whr_rear_wheel.wheel_mark_inner  &
   color = RED
!
geometry create shape cylinder  &
   cylinder_name = .VI_Racer_RT.whr_rear_wheel.tire_tread  &
   center_marker = .VI_Racer_RT.whr_rear_wheel.geo_inr  &
   angle_extent = 360.0  &
   length = -200.0  &
   radius = 250.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whr_rear_wheel.tire_tread  &
   color = DARK_GRAY
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whr_rear_wheel.tire_sidewall1  &
   center_marker = .VI_Racer_RT.whr_rear_wheel.geo_inr  &
   angle_extent = 360.0  &
   length = 20.0  &
   top_radius = 210.0  &
   bottom_radius = 170.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whr_rear_wheel.tire_sidewall1  &
   color = DARK_GRAY
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whr_rear_wheel.tire_sidewall2  &
   center_marker = .VI_Racer_RT.whr_rear_wheel.geo_inr  &
   angle_extent = 360.0  &
   length = 20.0  &
   top_radius = 210.0  &
   bottom_radius = 250.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whr_rear_wheel.tire_sidewall2  &
   color = DARK_GRAY
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whr_rear_wheel.tire_sidewall3  &
   center_marker = .VI_Racer_RT.whr_rear_wheel.geo_otr  &
   angle_extent = 360.0  &
   length = 20.0  &
   top_radius = 210.0  &
   bottom_radius = 170.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whr_rear_wheel.tire_sidewall3  &
   color = DARK_GRAY
!
geometry create shape frustum  &
   frustum_name = .VI_Racer_RT.whr_rear_wheel.tire_sidewall4  &
   center_marker = .VI_Racer_RT.whr_rear_wheel.geo_otr  &
   angle_extent = 360.0  &
   length = 20.0  &
   top_radius = 210.0  &
   bottom_radius = 250.0  &
   side_count_for_body = 20  &
   segment_count_for_ends = 0
!
geometry attributes  &
   geometry_name = .VI_Racer_RT.whr_rear_wheel.tire_sidewall4  &
   color = DARK_GRAY
!
part attributes  &
   part_name = .VI_Racer_RT.whr_rear_wheel  &
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
   variable_name = .VI_Racer_RT.cil_front_wheel_center  &
   units = "length"  &
   real_value = 0.0, 700.0, 251.2
!
variable create  &
   variable_name = .VI_Racer_RT.cil_front_wheel_center.matching_name  &
   string_value = "wheel_center"
!
variable create  &
   variable_name = .VI_Racer_RT.cil_front_wheel_center.entity  &
   string_value = "location"
!
variable create  &
   variable_name = .VI_Racer_RT.cil_front_wheel_center.minor_role  &
   string_value = "front"
!
variable create  &
   variable_name = .VI_Racer_RT.cir_front_wheel_center  &
   units = "length"  &
   real_value = 0.0, -700.0, 251.2
!
variable create  &
   variable_name = .VI_Racer_RT.cir_front_wheel_center.matching_name  &
   string_value = "wheel_center"
!
variable create  &
   variable_name = .VI_Racer_RT.cir_front_wheel_center.entity  &
   string_value = "location"
!
variable create  &
   variable_name = .VI_Racer_RT.cir_front_wheel_center.minor_role  &
   string_value = "front"
!
variable create  &
   variable_name = .VI_Racer_RT.cil_rear_wheel_center  &
   units = "length"  &
   real_value = -1542.4, 700.0, 250.0
!
variable create  &
   variable_name = .VI_Racer_RT.cil_rear_wheel_center.matching_name  &
   string_value = "wheel_center"
!
variable create  &
   variable_name = .VI_Racer_RT.cil_rear_wheel_center.entity  &
   string_value = "location"
!
variable create  &
   variable_name = .VI_Racer_RT.cil_rear_wheel_center.minor_role  &
   string_value = "rear"
!
variable create  &
   variable_name = .VI_Racer_RT.cir_rear_wheel_center  &
   units = "length"  &
   real_value = -1542.4, -700.0, 250.0
!
variable create  &
   variable_name = .VI_Racer_RT.cir_rear_wheel_center.matching_name  &
   string_value = "wheel_center"
!
variable create  &
   variable_name = .VI_Racer_RT.cir_rear_wheel_center.entity  &
   string_value = "location"
!
variable create  &
   variable_name = .VI_Racer_RT.cir_rear_wheel_center.minor_role  &
   string_value = "rear"
!
variable create  &
   variable_name = .VI_Racer_RT.cil_front_toe_angle  &
   units = "no_units"  &
   real_value = 0.0
!
variable create  &
   variable_name = .VI_Racer_RT.cil_front_toe_angle.matching_name  &
   string_value = "toe_angle"
!
variable create  &
   variable_name = .VI_Racer_RT.cil_front_toe_angle.entity  &
   string_value = "parameter_real"
!
variable create  &
   variable_name = .VI_Racer_RT.cil_front_toe_angle.minor_role  &
   string_value = "front"
!
variable create  &
   variable_name = .VI_Racer_RT.cir_front_toe_angle  &
   units = "no_units"  &
   real_value = 0.0
!
variable create  &
   variable_name = .VI_Racer_RT.cir_front_toe_angle.matching_name  &
   string_value = "toe_angle"
!
variable create  &
   variable_name = .VI_Racer_RT.cir_front_toe_angle.entity  &
   string_value = "parameter_real"
!
variable create  &
   variable_name = .VI_Racer_RT.cir_front_toe_angle.minor_role  &
   string_value = "front"
!
variable create  &
   variable_name = .VI_Racer_RT.cil_front_camber_angle  &
   units = "no_units"  &
   real_value = 0.0
!
variable create  &
   variable_name = .VI_Racer_RT.cil_front_camber_angle.matching_name  &
   string_value = "camber_angle"
!
variable create  &
   variable_name = .VI_Racer_RT.cil_front_camber_angle.entity  &
   string_value = "parameter_real"
!
variable create  &
   variable_name = .VI_Racer_RT.cil_front_camber_angle.minor_role  &
   string_value = "front"
!
variable create  &
   variable_name = .VI_Racer_RT.cir_front_camber_angle  &
   units = "no_units"  &
   real_value = 0.0
!
variable create  &
   variable_name = .VI_Racer_RT.cir_front_camber_angle.matching_name  &
   string_value = "camber_angle"
!
variable create  &
   variable_name = .VI_Racer_RT.cir_front_camber_angle.entity  &
   string_value = "parameter_real"
!
variable create  &
   variable_name = .VI_Racer_RT.cir_front_camber_angle.minor_role  &
   string_value = "front"
!
variable create  &
   variable_name = .VI_Racer_RT.cil_rear_camber_angle  &
   units = "no_units"  &
   real_value = 0.0
!
variable create  &
   variable_name = .VI_Racer_RT.cil_rear_camber_angle.matching_name  &
   string_value = "camber_angle"
!
variable create  &
   variable_name = .VI_Racer_RT.cil_rear_camber_angle.entity  &
   string_value = "parameter_real"
!
variable create  &
   variable_name = .VI_Racer_RT.cil_rear_camber_angle.minor_role  &
   string_value = "rear"
!
variable create  &
   variable_name = .VI_Racer_RT.cir_rear_camber_angle  &
   units = "no_units"  &
   real_value = 0.0
!
variable create  &
   variable_name = .VI_Racer_RT.cir_rear_camber_angle.matching_name  &
   string_value = "camber_angle"
!
variable create  &
   variable_name = .VI_Racer_RT.cir_rear_camber_angle.entity  &
   string_value = "parameter_real"
!
variable create  &
   variable_name = .VI_Racer_RT.cir_rear_camber_angle.minor_role  &
   string_value = "rear"
!
variable create  &
   variable_name = .VI_Racer_RT.cil_rear_toe_angle  &
   units = "no_units"  &
   real_value = 0.0
!
variable create  &
   variable_name = .VI_Racer_RT.cil_rear_toe_angle.matching_name  &
   string_value = "toe_angle"
!
variable create  &
   variable_name = .VI_Racer_RT.cil_rear_toe_angle.entity  &
   string_value = "parameter_real"
!
variable create  &
   variable_name = .VI_Racer_RT.cil_rear_toe_angle.minor_role  &
   string_value = "rear"
!
variable create  &
   variable_name = .VI_Racer_RT.cir_rear_toe_angle  &
   units = "no_units"  &
   real_value = 0.0
!
variable create  &
   variable_name = .VI_Racer_RT.cir_rear_toe_angle.matching_name  &
   string_value = "toe_angle"
!
variable create  &
   variable_name = .VI_Racer_RT.cir_rear_toe_angle.entity  &
   string_value = "parameter_real"
!
variable create  &
   variable_name = .VI_Racer_RT.cir_rear_toe_angle.minor_role  &
   string_value = "rear"
!
variable create  &
   variable_name = .VI_Racer_RT.fl_tire_radius  &
   units = "length"  &
   real_value = 250.0
!
variable create  &
   variable_name = .VI_Racer_RT.fl_tire_width  &
   units = "length"  &
   real_value = 200.0
!
variable create  &
   variable_name = .VI_Racer_RT.fr_tire_radius  &
   units = "length"  &
   real_value = 250.0
!
variable create  &
   variable_name = .VI_Racer_RT.fr_tire_width  &
   units = "length"  &
   real_value = 200.0
!
variable create  &
   variable_name = .VI_Racer_RT.rl_tire_radius  &
   units = "length"  &
   real_value = 250.0
!
variable create  &
   variable_name = .VI_Racer_RT.rl_tire_width  &
   units = "length"  &
   real_value = 200.0
!
variable create  &
   variable_name = .VI_Racer_RT.rr_tire_radius  &
   units = "length"  &
   real_value = 250.0
!
variable create  &
   variable_name = .VI_Racer_RT.rr_tire_width  &
   units = "length"  &
   real_value = 200.0
!
variable create  &
   variable_name = .VI_Racer_RT.whl_front_wheel.center_offset  &
   units = "length"  &
   real_value = 0.0
!
variable create  &
   variable_name = .VI_Racer_RT.whr_front_wheel.center_offset  &
   units = "length"  &
   real_value = 0.0
!
variable create  &
   variable_name = .VI_Racer_RT.whl_rear_wheel.center_offset  &
   units = "length"  &
   real_value = 0.0
!
variable create  &
   variable_name = .VI_Racer_RT.whr_rear_wheel.center_offset  &
   units = "length"  &
   real_value = 0.0
!
!--------------------------- Expression definitions ---------------------------!
!
!
defaults coordinate_system  &
   default_coordinate_system = ground
!
material modify  &
   material_name = .VI_Racer_RT.steel  &
   youngs_modulus = (2.07E+011(Newton/meter**2))  &
   density = (7801.0(kg/meter**3))
!
marker modify  &
   marker_name = .VI_Racer_RT.ges_chassis.inertia_frame  &
   location =   &
      (LOC_RELATIVE_TO({0, 0, 0}, .VI_Racer_RT.ges_chassis.cm))  &
   orientation =   &
      (ORI_RELATIVE_TO({0, 0, 0}, .VI_Racer_RT.ges_chassis))  &
   relative_to = .VI_Racer_RT.ges_chassis
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.ground
!
marker modify  &
   marker_name = .VI_Racer_RT.ges_chassis.fwl  &
   location =   &
      (.VI_Racer_RT.cil_front_wheel_center)  &
   orientation =   &
      (ORI_RELATIVE_TO({180d - .VI_Racer_RT.cil_front_toe_angle, -90d - .VI_Racer_RT.cil_front_camber_angle, 180d}, .VI_Racer_RT.ground.origo))  &
   relative_to = .VI_Racer_RT.ges_chassis
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.ground
!
marker modify  &
   marker_name = .VI_Racer_RT.ges_chassis.rwl  &
   location =   &
      (.VI_Racer_RT.cil_rear_wheel_center)  &
   orientation =   &
      (ORI_RELATIVE_TO({180d - .VI_Racer_RT.cil_rear_toe_angle, -90d - .VI_Racer_RT.cil_rear_camber_angle, 180d}, .VI_Racer_RT.ground.origo))  &
   relative_to = .VI_Racer_RT.ges_chassis
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.ground
!
marker modify  &
   marker_name = .VI_Racer_RT.ges_chassis.rwr  &
   location =   &
      (.VI_Racer_RT.cir_rear_wheel_center)  &
   orientation =   &
      (ORI_RELATIVE_TO({180d - .VI_Racer_RT.cir_rear_toe_angle, -90d - .VI_Racer_RT.cir_rear_camber_angle, 180d}, .VI_Racer_RT.ground.origo))  &
   relative_to = .VI_Racer_RT.ges_chassis
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.ground
!
marker modify  &
   marker_name = .VI_Racer_RT.ges_chassis.fwr  &
   location =   &
      (.VI_Racer_RT.cir_front_wheel_center)  &
   orientation =   &
      (ORI_RELATIVE_TO({180d - .VI_Racer_RT.cir_front_toe_angle, -90d - .VI_Racer_RT.cir_front_camber_angle, 180d}, .VI_Racer_RT.ground.origo))  &
   relative_to = .VI_Racer_RT.ges_chassis
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.ground
!
marker modify  &
   marker_name = .VI_Racer_RT.ges_engine.inertia_frame  &
   location =   &
      (LOC_RELATIVE_TO({0, 0, 0}, .VI_Racer_RT.ges_engine.cm))  &
   orientation =   &
      (ORI_RELATIVE_TO({0, 0, 0}, .VI_Racer_RT.ges_engine))  &
   relative_to = .VI_Racer_RT.ges_engine
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.ground
!
part modify rigid_body name_and_position  &
   part_name = .VI_Racer_RT.whl_front_wheel  &
   location =   &
      (LOC_RELATIVE_TO({0, 0, 0}, .VI_Racer_RT.ges_chassis.fwl))
!
marker modify  &
   marker_name = .VI_Racer_RT.whl_front_wheel.tire_i  &
   location =   &
      (LOC_RELATIVE_TO({0, 0, 0}, .VI_Racer_RT.ges_chassis.fwl))  &
   orientation =   &
      (ORI_RELATIVE_TO({0, 0, 0}, .VI_Racer_RT.ges_chassis.fwl))  &
   relative_to = .VI_Racer_RT.whl_front_wheel
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.ground
!
marker modify  &
   marker_name = .VI_Racer_RT.whl_front_wheel.geo_ctr  &
   location =   &
      (LOC_RELATIVE_TO({0, 0, .VI_Racer_RT.whl_front_wheel.center_offset - 0.1 * .VI_Racer_RT.fl_tire_width}, .VI_Racer_RT.whl_front_wheel.tire_i))  &
   relative_to = .VI_Racer_RT.whl_front_wheel
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.ground
!
marker modify  &
   marker_name = .VI_Racer_RT.whl_front_wheel.geo_inr  &
   location =   &
      (LOC_RELATIVE_TO({0, 0, -.VI_Racer_RT.fl_tire_width / 2}, .VI_Racer_RT.whl_front_wheel.tire_i))  &
   orientation =   &
      (ORI_RELATIVE_TO({0, 180d, 0}, .VI_Racer_RT.whl_front_wheel.tire_i))  &
   relative_to = .VI_Racer_RT.whl_front_wheel
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.ground
!
marker modify  &
   marker_name = .VI_Racer_RT.whl_front_wheel.geo_otr  &
   location =   &
      (LOC_RELATIVE_TO({0, 0, .VI_Racer_RT.fl_tire_width / 2}, .VI_Racer_RT.whl_front_wheel.tire_i))  &
   relative_to = .VI_Racer_RT.whl_front_wheel
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.ground
!
geometry modify shape cylinder  &
   cylinder_name = .VI_Racer_RT.whl_front_wheel.wheel_hub  &
   angle_extent = (360.0(deg))  &
   length = (0.2 * .VI_Racer_RT.fl_tire_width)  &
   radius = (.VI_Racer_RT.fl_tire_radius - .VI_Racer_RT.fl_tire_width * 0.4 - 0.1 * .VI_Racer_RT.fl_tire_radius)
!
geometry modify shape cylinder  &
   cylinder_name = .VI_Racer_RT.whl_front_wheel.wheel_rim  &
   angle_extent = (360.0(deg))  &
   length = (-.VI_Racer_RT.fl_tire_width)  &
   radius = (.VI_Racer_RT.fl_tire_radius - .VI_Racer_RT.fl_tire_width * 0.4 - 0.1 * .VI_Racer_RT.fl_tire_radius)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whl_front_wheel.wheel_inner1  &
   angle_extent = (360.0(deg))  &
   top_radius = (.VI_Racer_RT.fl_tire_radius - .VI_Racer_RT.fl_tire_width * 0.4 - 0.1 * .VI_Racer_RT.fl_tire_radius)  &
   bottom_radius = (.VI_Racer_RT.fl_tire_radius - .VI_Racer_RT.fl_tire_width * 0.4)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whl_front_wheel.wheel_outer1  &
   angle_extent = (360.0(deg))  &
   top_radius = (.VI_Racer_RT.fl_tire_radius - .VI_Racer_RT.fl_tire_width * 0.4 - 0.1 * .VI_Racer_RT.fl_tire_radius)  &
   bottom_radius = (.VI_Racer_RT.fl_tire_radius - .VI_Racer_RT.fl_tire_width * 0.4)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whl_front_wheel.wheel_mark_outer  &
   angle_extent = (20.0(deg))  &
   length = (2.0(mm))  &
   bottom_radius = (.VI_Racer_RT.fl_tire_radius - .VI_Racer_RT.fl_tire_width * 0.4)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whl_front_wheel.wheel_mark_inner  &
   angle_extent = (-20.0(deg))  &
   length = (-2.0(mm))  &
   bottom_radius = (.VI_Racer_RT.fl_tire_radius - .VI_Racer_RT.fl_tire_width * 0.4)
!
geometry modify shape cylinder  &
   cylinder_name = .VI_Racer_RT.whl_front_wheel.tire_tread  &
   angle_extent = (360.0(deg))  &
   length = (-.VI_Racer_RT.fl_tire_width)  &
   radius = (.VI_Racer_RT.fl_tire_radius)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whl_front_wheel.tire_sidewall1  &
   angle_extent = (360.0(deg))  &
   length = (0.25 * (.VI_Racer_RT.fl_tire_width * 0.4))  &
   top_radius = (.VI_Racer_RT.fl_tire_radius - 0.5 * (.VI_Racer_RT.fl_tire_width * 0.4))  &
   bottom_radius = (.VI_Racer_RT.fl_tire_radius - .VI_Racer_RT.fl_tire_width * 0.4)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whl_front_wheel.tire_sidewall2  &
   angle_extent = (360.0(deg))  &
   length = (0.25 * (.VI_Racer_RT.fl_tire_width * 0.4))  &
   top_radius = (.VI_Racer_RT.fl_tire_radius - 0.5 * (.VI_Racer_RT.fl_tire_width * 0.4))  &
   bottom_radius = (.VI_Racer_RT.fl_tire_radius)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whl_front_wheel.tire_sidewall3  &
   angle_extent = (360.0(deg))  &
   length = (0.25 * (.VI_Racer_RT.fl_tire_width * 0.4))  &
   top_radius = (.VI_Racer_RT.fl_tire_radius - 0.5 * (.VI_Racer_RT.fl_tire_width * 0.4))  &
   bottom_radius = (.VI_Racer_RT.fl_tire_radius - .VI_Racer_RT.fl_tire_width * 0.4)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whl_front_wheel.tire_sidewall4  &
   angle_extent = (360.0(deg))  &
   length = (0.25 * (.VI_Racer_RT.fl_tire_width * 0.4))  &
   top_radius = (.VI_Racer_RT.fl_tire_radius - 0.5 * (.VI_Racer_RT.fl_tire_width * 0.4))  &
   bottom_radius = (.VI_Racer_RT.fl_tire_radius)
!
part modify rigid_body name_and_position  &
   part_name = .VI_Racer_RT.whr_front_wheel  &
   location =   &
      (LOC_RELATIVE_TO({0, 0, 0}, .VI_Racer_RT.ges_chassis.fwr))
!
marker modify  &
   marker_name = .VI_Racer_RT.whr_front_wheel.tire_i  &
   location =   &
      (LOC_RELATIVE_TO({0, 0, 0}, .VI_Racer_RT.ges_chassis.fwr))  &
   orientation =   &
      (ORI_RELATIVE_TO({0, 0, 0}, .VI_Racer_RT.ges_chassis.fwr))  &
   relative_to = .VI_Racer_RT.whr_front_wheel
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.ground
!
marker modify  &
   marker_name = .VI_Racer_RT.whr_front_wheel.geo_ctr  &
   location =   &
      (LOC_RELATIVE_TO({0, 0, .VI_Racer_RT.whr_front_wheel.center_offset - 0.1 * .VI_Racer_RT.fr_tire_width}, .VI_Racer_RT.whr_front_wheel.tire_i))  &
   relative_to = .VI_Racer_RT.whr_front_wheel
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.ground
!
marker modify  &
   marker_name = .VI_Racer_RT.whr_front_wheel.geo_inr  &
   location =   &
      (LOC_RELATIVE_TO({0, 0, -.VI_Racer_RT.fr_tire_width / 2}, .VI_Racer_RT.whr_front_wheel.tire_i))  &
   orientation =   &
      (ORI_RELATIVE_TO({0, 180d, 0}, .VI_Racer_RT.whr_front_wheel.tire_i))  &
   relative_to = .VI_Racer_RT.whr_front_wheel
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.ground
!
marker modify  &
   marker_name = .VI_Racer_RT.whr_front_wheel.geo_otr  &
   location =   &
      (LOC_RELATIVE_TO({0, 0, .VI_Racer_RT.fr_tire_width / 2}, .VI_Racer_RT.whr_front_wheel.tire_i))  &
   relative_to = .VI_Racer_RT.whr_front_wheel
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.ground
!
geometry modify shape cylinder  &
   cylinder_name = .VI_Racer_RT.whr_front_wheel.wheel_hub  &
   angle_extent = (360.0(deg))  &
   length = (0.2 * .VI_Racer_RT.fr_tire_width)  &
   radius = (.VI_Racer_RT.fr_tire_radius - .VI_Racer_RT.fr_tire_width * 0.4 - 0.1 * .VI_Racer_RT.fr_tire_radius)
!
geometry modify shape cylinder  &
   cylinder_name = .VI_Racer_RT.whr_front_wheel.wheel_rim  &
   angle_extent = (360.0(deg))  &
   length = (-.VI_Racer_RT.fr_tire_width)  &
   radius = (.VI_Racer_RT.fr_tire_radius - .VI_Racer_RT.fr_tire_width * 0.4 - 0.1 * .VI_Racer_RT.fr_tire_radius)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whr_front_wheel.wheel_inner1  &
   angle_extent = (360.0(deg))  &
   top_radius = (.VI_Racer_RT.fr_tire_radius - .VI_Racer_RT.fr_tire_width * 0.4 - 0.1 * .VI_Racer_RT.fr_tire_radius)  &
   bottom_radius = (.VI_Racer_RT.fr_tire_radius - .VI_Racer_RT.fr_tire_width * 0.4)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whr_front_wheel.wheel_outer1  &
   angle_extent = (360.0(deg))  &
   top_radius = (.VI_Racer_RT.fr_tire_radius - .VI_Racer_RT.fr_tire_width * 0.4 - 0.1 * .VI_Racer_RT.fr_tire_radius)  &
   bottom_radius = (.VI_Racer_RT.fr_tire_radius - .VI_Racer_RT.fr_tire_width * 0.4)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whr_front_wheel.wheel_mark_outer  &
   angle_extent = (20.0(deg))  &
   length = (2.0(mm))  &
   bottom_radius = (.VI_Racer_RT.fr_tire_radius - .VI_Racer_RT.fr_tire_width * 0.4)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whr_front_wheel.wheel_mark_inner  &
   angle_extent = (-20.0(deg))  &
   length = (-2.0(mm))  &
   bottom_radius = (.VI_Racer_RT.fr_tire_radius - .VI_Racer_RT.fr_tire_width * 0.4)
!
geometry modify shape cylinder  &
   cylinder_name = .VI_Racer_RT.whr_front_wheel.tire_tread  &
   angle_extent = (360.0(deg))  &
   length = (-.VI_Racer_RT.fr_tire_width)  &
   radius = (.VI_Racer_RT.fr_tire_radius)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whr_front_wheel.tire_sidewall1  &
   angle_extent = (360.0(deg))  &
   length = (0.25 * (.VI_Racer_RT.fr_tire_width * 0.4))  &
   top_radius = (.VI_Racer_RT.fr_tire_radius - 0.5 * (.VI_Racer_RT.fr_tire_width * 0.4))  &
   bottom_radius = (.VI_Racer_RT.fr_tire_radius - .VI_Racer_RT.fr_tire_width * 0.4)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whr_front_wheel.tire_sidewall2  &
   angle_extent = (360.0(deg))  &
   length = (0.25 * (.VI_Racer_RT.fr_tire_width * 0.4))  &
   top_radius = (.VI_Racer_RT.fr_tire_radius - 0.5 * (.VI_Racer_RT.fr_tire_width * 0.4))  &
   bottom_radius = (.VI_Racer_RT.fr_tire_radius)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whr_front_wheel.tire_sidewall3  &
   angle_extent = (360.0(deg))  &
   length = (0.25 * (.VI_Racer_RT.fr_tire_width * 0.4))  &
   top_radius = (.VI_Racer_RT.fr_tire_radius - 0.5 * (.VI_Racer_RT.fr_tire_width * 0.4))  &
   bottom_radius = (.VI_Racer_RT.fr_tire_radius - .VI_Racer_RT.fr_tire_width * 0.4)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whr_front_wheel.tire_sidewall4  &
   angle_extent = (360.0(deg))  &
   length = (0.25 * (.VI_Racer_RT.fr_tire_width * 0.4))  &
   top_radius = (.VI_Racer_RT.fr_tire_radius - 0.5 * (.VI_Racer_RT.fr_tire_width * 0.4))  &
   bottom_radius = (.VI_Racer_RT.fr_tire_radius)
!
part modify rigid_body name_and_position  &
   part_name = .VI_Racer_RT.whl_rear_wheel  &
   location =   &
      (LOC_RELATIVE_TO({0, 0, 0}, .VI_Racer_RT.ges_chassis.rwl))
!
marker modify  &
   marker_name = .VI_Racer_RT.whl_rear_wheel.tire_i  &
   location =   &
      (LOC_RELATIVE_TO({0, 0, 0}, .VI_Racer_RT.ges_chassis.rwl))  &
   orientation =   &
      (ORI_RELATIVE_TO({0, 0, 0}, .VI_Racer_RT.ges_chassis.rwl))  &
   relative_to = .VI_Racer_RT.whl_rear_wheel
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.ground
!
marker modify  &
   marker_name = .VI_Racer_RT.whl_rear_wheel.geo_ctr  &
   location =   &
      (LOC_RELATIVE_TO({0, 0, .VI_Racer_RT.whl_rear_wheel.center_offset - 0.1 * .VI_Racer_RT.rl_tire_width}, .VI_Racer_RT.whl_rear_wheel.tire_i))  &
   relative_to = .VI_Racer_RT.whl_rear_wheel
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.ground
!
marker modify  &
   marker_name = .VI_Racer_RT.whl_rear_wheel.geo_inr  &
   location =   &
      (LOC_RELATIVE_TO({0, 0, -.VI_Racer_RT.rl_tire_width / 2}, .VI_Racer_RT.whl_rear_wheel.tire_i))  &
   orientation =   &
      (ORI_RELATIVE_TO({0, 180d, 0}, .VI_Racer_RT.whl_rear_wheel.tire_i))  &
   relative_to = .VI_Racer_RT.whl_rear_wheel
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.ground
!
marker modify  &
   marker_name = .VI_Racer_RT.whl_rear_wheel.geo_otr  &
   location =   &
      (LOC_RELATIVE_TO({0, 0, .VI_Racer_RT.rl_tire_width / 2}, .VI_Racer_RT.whl_rear_wheel.tire_i))  &
   relative_to = .VI_Racer_RT.whl_rear_wheel
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.ground
!
geometry modify shape cylinder  &
   cylinder_name = .VI_Racer_RT.whl_rear_wheel.wheel_hub  &
   angle_extent = (360.0(deg))  &
   length = (0.2 * .VI_Racer_RT.rl_tire_width)  &
   radius = (.VI_Racer_RT.rl_tire_radius - .VI_Racer_RT.rl_tire_width * 0.4 - 0.1 * .VI_Racer_RT.rl_tire_radius)
!
geometry modify shape cylinder  &
   cylinder_name = .VI_Racer_RT.whl_rear_wheel.wheel_rim  &
   angle_extent = (360.0(deg))  &
   length = (-.VI_Racer_RT.rl_tire_width)  &
   radius = (.VI_Racer_RT.rl_tire_radius - .VI_Racer_RT.rl_tire_width * 0.4 - 0.1 * .VI_Racer_RT.rl_tire_radius)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whl_rear_wheel.wheel_inner1  &
   angle_extent = (360.0(deg))  &
   top_radius = (.VI_Racer_RT.rl_tire_radius - .VI_Racer_RT.rl_tire_width * 0.4 - 0.1 * .VI_Racer_RT.rl_tire_radius)  &
   bottom_radius = (.VI_Racer_RT.rl_tire_radius - .VI_Racer_RT.rl_tire_width * 0.4)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whl_rear_wheel.wheel_outer1  &
   angle_extent = (360.0(deg))  &
   top_radius = (.VI_Racer_RT.rl_tire_radius - .VI_Racer_RT.rl_tire_width * 0.4 - 0.1 * .VI_Racer_RT.rl_tire_radius)  &
   bottom_radius = (.VI_Racer_RT.rl_tire_radius - .VI_Racer_RT.rl_tire_width * 0.4)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whl_rear_wheel.wheel_mark_outer  &
   angle_extent = (20.0(deg))  &
   length = (2.0(mm))  &
   bottom_radius = (.VI_Racer_RT.rl_tire_radius - .VI_Racer_RT.rl_tire_width * 0.4)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whl_rear_wheel.wheel_mark_inner  &
   angle_extent = (-20.0(deg))  &
   length = (-2.0(mm))  &
   bottom_radius = (.VI_Racer_RT.rl_tire_radius - .VI_Racer_RT.rl_tire_width * 0.4)
!
geometry modify shape cylinder  &
   cylinder_name = .VI_Racer_RT.whl_rear_wheel.tire_tread  &
   angle_extent = (360.0(deg))  &
   length = (-.VI_Racer_RT.rl_tire_width)  &
   radius = (.VI_Racer_RT.rl_tire_radius)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whl_rear_wheel.tire_sidewall1  &
   angle_extent = (360.0(deg))  &
   length = (0.25 * (.VI_Racer_RT.rl_tire_width * 0.4))  &
   top_radius = (.VI_Racer_RT.rl_tire_radius - 0.5 * (.VI_Racer_RT.rl_tire_width * 0.4))  &
   bottom_radius = (.VI_Racer_RT.rl_tire_radius - .VI_Racer_RT.rl_tire_width * 0.4)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whl_rear_wheel.tire_sidewall2  &
   angle_extent = (360.0(deg))  &
   length = (0.25 * (.VI_Racer_RT.rl_tire_width * 0.4))  &
   top_radius = (.VI_Racer_RT.rl_tire_radius - 0.5 * (.VI_Racer_RT.rl_tire_width * 0.4))  &
   bottom_radius = (.VI_Racer_RT.rl_tire_radius)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whl_rear_wheel.tire_sidewall3  &
   angle_extent = (360.0(deg))  &
   length = (0.25 * (.VI_Racer_RT.rl_tire_width * 0.4))  &
   top_radius = (.VI_Racer_RT.rl_tire_radius - 0.5 * (.VI_Racer_RT.rl_tire_width * 0.4))  &
   bottom_radius = (.VI_Racer_RT.rl_tire_radius - .VI_Racer_RT.rl_tire_width * 0.4)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whl_rear_wheel.tire_sidewall4  &
   angle_extent = (360.0(deg))  &
   length = (0.25 * (.VI_Racer_RT.rl_tire_width * 0.4))  &
   top_radius = (.VI_Racer_RT.rl_tire_radius - 0.5 * (.VI_Racer_RT.rl_tire_width * 0.4))  &
   bottom_radius = (.VI_Racer_RT.rl_tire_radius)
!
part modify rigid_body name_and_position  &
   part_name = .VI_Racer_RT.whr_rear_wheel  &
   location =   &
      (LOC_RELATIVE_TO({0, 0, 0}, .VI_Racer_RT.ges_chassis.rwr))
!
marker modify  &
   marker_name = .VI_Racer_RT.whr_rear_wheel.tire_i  &
   location =   &
      (LOC_RELATIVE_TO({0, 0, 0}, .VI_Racer_RT.ges_chassis.rwr))  &
   orientation =   &
      (ORI_RELATIVE_TO({0, 0, 0}, .VI_Racer_RT.ges_chassis.rwr))  &
   relative_to = .VI_Racer_RT.whr_rear_wheel
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.ground
!
marker modify  &
   marker_name = .VI_Racer_RT.whr_rear_wheel.geo_ctr  &
   location =   &
      (LOC_RELATIVE_TO({0, 0, .VI_Racer_RT.whr_rear_wheel.center_offset - 0.1 * .VI_Racer_RT.rr_tire_width}, .VI_Racer_RT.whr_rear_wheel.tire_i))  &
   relative_to = .VI_Racer_RT.whr_rear_wheel
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.ground
!
marker modify  &
   marker_name = .VI_Racer_RT.whr_rear_wheel.geo_inr  &
   location =   &
      (LOC_RELATIVE_TO({0, 0, -.VI_Racer_RT.rr_tire_width / 2}, .VI_Racer_RT.whr_rear_wheel.tire_i))  &
   orientation =   &
      (ORI_RELATIVE_TO({0, 180d, 0}, .VI_Racer_RT.whr_rear_wheel.tire_i))  &
   relative_to = .VI_Racer_RT.whr_rear_wheel
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.ground
!
marker modify  &
   marker_name = .VI_Racer_RT.whr_rear_wheel.geo_otr  &
   location =   &
      (LOC_RELATIVE_TO({0, 0, .VI_Racer_RT.rr_tire_width / 2}, .VI_Racer_RT.whr_rear_wheel.tire_i))  &
   relative_to = .VI_Racer_RT.whr_rear_wheel
!
defaults coordinate_system  &
   default_coordinate_system = .VI_Racer_RT.ground
!
geometry modify shape cylinder  &
   cylinder_name = .VI_Racer_RT.whr_rear_wheel.wheel_hub  &
   angle_extent = (360.0(deg))  &
   length = (0.2 * .VI_Racer_RT.rr_tire_width)  &
   radius = (.VI_Racer_RT.rr_tire_radius - .VI_Racer_RT.rr_tire_width * 0.4 - 0.1 * .VI_Racer_RT.rr_tire_radius)
!
geometry modify shape cylinder  &
   cylinder_name = .VI_Racer_RT.whr_rear_wheel.wheel_rim  &
   angle_extent = (360.0(deg))  &
   length = (-.VI_Racer_RT.rr_tire_width)  &
   radius = (.VI_Racer_RT.rr_tire_radius - .VI_Racer_RT.rr_tire_width * 0.4 - 0.1 * .VI_Racer_RT.rr_tire_radius)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whr_rear_wheel.wheel_inner1  &
   angle_extent = (360.0(deg))  &
   top_radius = (.VI_Racer_RT.rr_tire_radius - .VI_Racer_RT.rr_tire_width * 0.4 - 0.1 * .VI_Racer_RT.rr_tire_radius)  &
   bottom_radius = (.VI_Racer_RT.rr_tire_radius - .VI_Racer_RT.rr_tire_width * 0.4)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whr_rear_wheel.wheel_outer1  &
   angle_extent = (360.0(deg))  &
   top_radius = (.VI_Racer_RT.rr_tire_radius - .VI_Racer_RT.rr_tire_width * 0.4 - 0.1 * .VI_Racer_RT.rr_tire_radius)  &
   bottom_radius = (.VI_Racer_RT.rr_tire_radius - .VI_Racer_RT.rr_tire_width * 0.4)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whr_rear_wheel.wheel_mark_outer  &
   angle_extent = (20.0(deg))  &
   length = (2.0(mm))  &
   bottom_radius = (.VI_Racer_RT.rr_tire_radius - .VI_Racer_RT.rr_tire_width * 0.4)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whr_rear_wheel.wheel_mark_inner  &
   angle_extent = (-20.0(deg))  &
   length = (-2.0(mm))  &
   bottom_radius = (.VI_Racer_RT.rr_tire_radius - .VI_Racer_RT.rr_tire_width * 0.4)
!
geometry modify shape cylinder  &
   cylinder_name = .VI_Racer_RT.whr_rear_wheel.tire_tread  &
   angle_extent = (360.0(deg))  &
   length = (-.VI_Racer_RT.rr_tire_width)  &
   radius = (.VI_Racer_RT.rr_tire_radius)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whr_rear_wheel.tire_sidewall1  &
   angle_extent = (360.0(deg))  &
   length = (0.25 * (.VI_Racer_RT.rr_tire_width * 0.4))  &
   top_radius = (.VI_Racer_RT.rr_tire_radius - 0.5 * (.VI_Racer_RT.rr_tire_width * 0.4))  &
   bottom_radius = (.VI_Racer_RT.rr_tire_radius - .VI_Racer_RT.rr_tire_width * 0.4)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whr_rear_wheel.tire_sidewall2  &
   angle_extent = (360.0(deg))  &
   length = (0.25 * (.VI_Racer_RT.rr_tire_width * 0.4))  &
   top_radius = (.VI_Racer_RT.rr_tire_radius - 0.5 * (.VI_Racer_RT.rr_tire_width * 0.4))  &
   bottom_radius = (.VI_Racer_RT.rr_tire_radius)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whr_rear_wheel.tire_sidewall3  &
   angle_extent = (360.0(deg))  &
   length = (0.25 * (.VI_Racer_RT.rr_tire_width * 0.4))  &
   top_radius = (.VI_Racer_RT.rr_tire_radius - 0.5 * (.VI_Racer_RT.rr_tire_width * 0.4))  &
   bottom_radius = (.VI_Racer_RT.rr_tire_radius - .VI_Racer_RT.rr_tire_width * 0.4)
!
geometry modify shape frustum  &
   frustum_name = .VI_Racer_RT.whr_rear_wheel.tire_sidewall4  &
   angle_extent = (360.0(deg))  &
   length = (0.25 * (.VI_Racer_RT.rr_tire_width * 0.4))  &
   top_radius = (.VI_Racer_RT.rr_tire_radius - 0.5 * (.VI_Racer_RT.rr_tire_width * 0.4))  &
   bottom_radius = (.VI_Racer_RT.rr_tire_radius)
!
model display  &
   model_name = VI_Racer_RT
