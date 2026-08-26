<?xml version="1.0" encoding="utf-8"?>
<VIPLOT>
  <viframework::viobjects::PlotConfiguration fixedTimeSlice="0" name="full_vehicle_cfg">
    <viframework::viobjects::PlotPage name="G">
      <viframework::viobjects::PlotItem column="0" columnSpan="1" name="" row="0" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="chassis_accelerations.longitudinal"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="0" columnSpan="1" name="" row="1" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="chassis_accelerations.lateral"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
    </viframework::viobjects::PlotPage>
    <viframework::viobjects::PlotPage name="Motor">
      <viframework::viobjects::PlotItem column="0" columnSpan="1" name="" row="0" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="differential_torques.output_torque_left_rear"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="differential_torques.output_torque_right_rear"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="motor_to_gearbox.torque"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="transmission.torque"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="1" columnSpan="1" name="" row="0" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="motor_to_gearbox.engine_rpm"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="0" columnSpan="1" name="" row="1" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="motor_to_gearbox.Power_KW"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="1" columnSpan="1" name="" row="1" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="driver_demands.throttle"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="driving_machine_monitor.driver_brake"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
    </viframework::viobjects::PlotPage>
    <viframework::viobjects::PlotPage name="Pitch/Roll/Yaw">
      <viframework::viobjects::PlotItem column="0" columnSpan="1" name="" row="0" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="chassis_displacements.pitch_wrt_road"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="1" columnSpan="1" name="" row="0" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="chassis_displacements.roll"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="0" columnSpan="1" name="" row="1" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="Vehicle_States.yaw_angular_acc_wrt_road"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="1" columnSpan="1" name="" row="1" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="chassis_accelerations.lateral"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="chassis_accelerations.longitudinal"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
    </viframework::viobjects::PlotPage>
    <viframework::viobjects::PlotPage name="Accuum">
      <viframework::viobjects::PlotItem column="0" columnSpan="1" name="" row="0" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="BatteryInternal.Charge_Voltage"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="BatteryInternal.Discharge_Voltage"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="BatteryInternal.Voltage"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="1" columnSpan="1" name="" row="0" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="BatteryInternal.SOC"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="0" columnSpan="1" name="" row="1" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="BatteryInternal.Current"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="1" columnSpan="1" name="" row="1" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="Vehicle.Origin_Distance_Traveled"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
    </viframework::viobjects::PlotPage>
    <viframework::viobjects::PlotPage name="Spring Compression">
      <viframework::viobjects::PlotItem column="0" columnSpan="1" name="" row="0" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="nsl_ride_spring_data.displacement_front"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="1" columnSpan="1" name="" row="0" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="nsr_ride_spring_data.displacement_front"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="0" columnSpan="1" name="" row="1" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="nsl_ride_spring_data.displacement_rear"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="1" columnSpan="1" name="" row="1" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="nsr_ride_spring_data.displacement_rear"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
    </viframework::viobjects::PlotPage>
    <viframework::viobjects::PlotPage name="Camber">
      <viframework::viobjects::PlotItem column="0" columnSpan="1" name="" row="0" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="wheel_angles.camber_wrt_road_L1"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="1" columnSpan="1" name="" row="0" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="wheel_angles.camber_wrt_road_R1"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="0" columnSpan="1" name="" row="1" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="wheel_angles.camber_wrt_road_L2"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="1" columnSpan="1" name="" row="1" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="wheel_angles.camber_wrt_road_R2"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
    </viframework::viobjects::PlotPage>
    <viframework::viobjects::PlotPage name="Steering">
      <viframework::viobjects::PlotItem column="0" columnSpan="1" name="" row="0" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="driver_demands.steering"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="til_wheel_tire_kinematics.lateral_slip_front"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="tir_wheel_tire_kinematics.lateral_slip_front"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="Wheel.Spindle_Steer.L1"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="Wheel.Spindle_Steer.R1"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="1" columnSpan="1" name="" row="0" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="Steering_System.Steering_Wheel_Torque"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="wheel_angles.toe_wrt_road_L1"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="wheel_angles.toe_wrt_road_R1"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="0" columnSpan="1" name="" row="1" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="chassis_accelerations.lateral"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="til_wheel_tire_kinematics.lateral_slip_front"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="tir_wheel_tire_kinematics.lateral_slip_front"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="1" columnSpan="1" name="" row="1" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="Steering_System.Rack_Force"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
    </viframework::viobjects::PlotPage>
    <viframework::viobjects::PlotPage name="Aero">
      <viframework::viobjects::PlotItem column="0" columnSpan="1" name="" row="0" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="aero_forces.drag_force"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="0" columnSpan="1" name="" row="1" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="aero_forces.front_downforce"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="aero_forces.rear_downforce"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
    </viframework::viobjects::PlotPage>
    <viframework::viobjects::PlotPage name="Tires">
      <viframework::viobjects::PlotItem column="0" columnSpan="1" name="" row="0" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="til_wheel_tire_forces.lateral_front"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="til_wheel_tire_forces.longitudinal_front"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="til_wheel_tire_forces.normal_front"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="1" columnSpan="1" name="" row="0" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="tir_wheel_tire_forces.lateral_front"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="tir_wheel_tire_forces.longitudinal_front"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="tir_wheel_tire_forces.normal_front"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="0" columnSpan="1" name="" row="1" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="til_wheel_tire_forces.lateral_rear"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="til_wheel_tire_forces.longitudinal_rear"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="til_wheel_tire_forces.normal_rear"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="1" columnSpan="1" name="" row="1" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="tir_wheel_tire_forces.lateral_rear"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="tir_wheel_tire_forces.longitudinal_rear"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="tir_wheel_tire_forces.normal_rear"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
    </viframework::viobjects::PlotPage>
    <viframework::viobjects::PlotPage name="Understeer">
      <viframework::viobjects::PlotItem column="0" columnSpan="1" name="" row="0" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="Vehicle.Understeer_Gradient"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="Vehicle.Understeer_Stability_Factor"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
    </viframework::viobjects::PlotPage>
    <viframework::viobjects::PlotPage name="Effective Rad">
      <viframework::viobjects::PlotItem column="0" columnSpan="1" name="" row="0" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="Tire.Effective_Rolling_Radius.L1"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="Tire.Effective_Rolling_Radius.L2"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="Tire.Effective_Rolling_Radius.R1"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="Tire.Effective_Rolling_Radius.R2"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="1" columnSpan="1" name="" row="0" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="Tire.Actual_Tread_Speed.L1"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="Tire.Actual_Tread_Speed.L2"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="Tire.Actual_Tread_Speed.R1"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="Tire.Actual_Tread_Speed.R2"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="0" columnSpan="1" name="" row="1" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="transmission.output_rpm"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="1" columnSpan="1" name="" row="1" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name=""></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name=""></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
    </viframework::viobjects::PlotPage>
    <viframework::viobjects::PlotPage name="Slip Ratio">
      <viframework::viobjects::PlotItem column="0" columnSpan="1" name="" row="0" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="til_wheel_tire_kinematics.longitudinal_slip_front"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="1" columnSpan="1" name="" row="0" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="chassis_accelerations.longitudinal"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="tir_wheel_tire_kinematics.longitudinal_slip_front"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="0" columnSpan="1" name="" row="1" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="til_wheel_tire_kinematics.longitudinal_slip_rear"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="1" columnSpan="1" name="" row="1" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="tir_wheel_tire_kinematics.longitudinal_slip_rear"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
    </viframework::viobjects::PlotPage>
    <viframework::viobjects::PlotPage name="Brake">
      <viframework::viobjects::PlotItem column="0" columnSpan="1" name="" row="0" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="Brake.Chamber_Pressure.L1"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="Brake.Chamber_Pressure.R1"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="1" columnSpan="1" name="" row="0" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="driver_demands.brake"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="0" columnSpan="1" name="" row="1" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="til_wheel_tire_forces.normal_front"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="til_wheel_tire_forces.normal_rear"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="1" columnSpan="1" name="" row="1" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="Tire.Ground_Surface_Peak_Friction_X.L1"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="Tire.Ground_Surface_Peak_Friction_X.L2"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
    </viframework::viobjects::PlotPage>
    <viframework::viobjects::PlotPage name="Height">
      <viframework::viobjects::PlotItem column="0" columnSpan="1" name="" row="0" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="rhl_front_setup_sensor_data.ride_height"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="rhr_front_setup_sensor_data.ride_height"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="rhs_rear_setup_sensor_data.ride_height"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="1" columnSpan="1" name="" row="0" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="Vehicle.front_ride_height_at_center_point"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="0" columnSpan="1" name="" row="1" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="Suspension.Roll_Center_Height.front"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="Suspension.Roll_Center_Height.rear"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="1" columnSpan="1" name="" row="1" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="Suspension.Roll_Center_Lateral_Displacement.front"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="Suspension.Roll_Center_Lateral_Displacement.rear"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
    </viframework::viobjects::PlotPage>
    <viframework::viobjects::PlotPage name="new page">
      <viframework::viobjects::PlotItem column="0" columnSpan="1" name="" row="0" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="til_wheel_tire_forces.lateral_front"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="1" columnSpan="1" name="" row="0" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="tir_wheel_tire_forces.lateral_front"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="0" columnSpan="1" name="" row="1" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="til_wheel_tire_forces.lateral_rear"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
      <viframework::viobjects::PlotItem column="1" columnSpan="1" name="" row="1" rowSpan="1">
        <viframework::viobjects::PlotComponent axis="0" name="time.TIME"></viframework::viobjects::PlotComponent>
        <viframework::viobjects::PlotComponent axis="1" name="tir_wheel_tire_forces.lateral_rear"></viframework::viobjects::PlotComponent>
      </viframework::viobjects::PlotItem>
    </viframework::viobjects::PlotPage>
  </viframework::viobjects::PlotConfiguration>
</VIPLOT>
