<?xml version="1.0" encoding="UTF-8"?>
<Results xmlns="http://www.mscsoftware.com/:xrf10">
<Bibliography>
<File schema="xrf" version="2.0.0.0" />
<Corporation author="VI-Grade" URI="http://www.vi-grade.com/" />
<Revision version="1" derivedFrom="-unknown-">
<Comment>
</Comment>
</Revision>
</Bibliography>
<Analysis name="DefaultRun" executionDate="2026-07-10 21:40:43" script="">
<ModelInfo title="VI-CarRealTime Vehicle Model" />
<Units angle="rad" length="m" mass="kg" time="sec" />
<StepMap name="map_001">
<Entity name="time" entType="Request">
<Component name="TIME" unitsValue="sec" id="1" />
</Entity>
<Entity name="Animator_Widget" entity="Animator_Widget" entType="Request">
<Component name="longitudinal_speed" unitsValue="" plotLabel="Velocity (km/h)" id="2" />
<Component name="engine_rpm" unitsValue="" plotLabel="RPM" id="3" />
</Entity>
<Entity name="BatteryInternal" entity="BatteryInternal" entType="Request">
<Component name="SOC" unitsValue="" plotLabel="percentage" id="4" />
<Component name="Current" unitsValue="" plotLabel="Ampere" id="5" />
<Component name="Voltage" unitsValue="" plotLabel="Volt" id="6" />
<Component name="Regenerative_Mode" unitsValue="" plotLabel="on" id="7" />
<Component name="Constant_Voltage" unitsValue="" plotLabel="Volt" id="8" />
<Component name="Exponential_Voltage" unitsValue="" plotLabel="Volt" id="9" />
<Component name="NonLinear_Voltage" unitsValue="" plotLabel="Volt" id="10" />
<Component name="Charge_Voltage" unitsValue="" plotLabel="Volt" id="11" />
<Component name="Discharge_Voltage" unitsValue="" plotLabel="Volt" id="12" />
<Component name="It" unitsValue="" plotLabel="Ampere*h" id="13" />
<Component name="It_sat" unitsValue="" plotLabel="Ampere*h" id="14" />
<Component name="I_star" unitsValue="" plotLabel="Ampere" id="15" />
<Component name="scaling" unitsValue="" plotLabel="" id="16" />
</Entity>
<Entity name="Brake.ABS_Activity" entity="Brake.ABS_Activity" entType="Request">
<Component name="L1" unitsValue="" plotLabel="ABS_Control_Activation (-)" id="17" />
<Component name="L2" unitsValue="" plotLabel="ABS_Control_Activation (-)" id="18" />
<Component name="R1" unitsValue="" plotLabel="ABS_Control_Activation (-)" id="19" />
<Component name="R2" unitsValue="" plotLabel="ABS_Control_Activation (-)" id="20" />
</Entity>
<Entity name="Brake.Brake_Moment" entity="Brake.Brake_Moment" entType="Request">
<Component name="L1" unitsValue="newton-meter" plotLabel="" id="21" />
<Component name="L2" unitsValue="newton-meter" plotLabel="" id="22" />
<Component name="R1" unitsValue="newton-meter" plotLabel="" id="23" />
<Component name="R2" unitsValue="newton-meter" plotLabel="" id="24" />
</Entity>
<Entity name="Brake.Chamber_Pressure" entity="Brake.Chamber_Pressure" entType="Request">
<Component name="L1" unitsValue="" plotLabel="Pressure (MPa)" id="25" />
<Component name="L2" unitsValue="" plotLabel="Pressure (MPa)" id="26" />
<Component name="R1" unitsValue="" plotLabel="Pressure (MPa)" id="27" />
<Component name="R2" unitsValue="" plotLabel="Pressure (MPa)" id="28" />
</Entity>
<Entity name="Brake.Locked_Damper_Moment" entity="Brake.Locked_Damper_Moment" entType="Request">
<Component name="L1" unitsValue="newton-meter" plotLabel="" id="29" />
<Component name="L2" unitsValue="newton-meter" plotLabel="" id="30" />
<Component name="R1" unitsValue="newton-meter" plotLabel="" id="31" />
<Component name="R2" unitsValue="newton-meter" plotLabel="" id="32" />
</Entity>
<Entity name="Brake.Locked_Moment" entity="Brake.Locked_Moment" entType="Request">
<Component name="L1" unitsValue="newton-meter" plotLabel="" id="33" />
<Component name="L2" unitsValue="newton-meter" plotLabel="" id="34" />
<Component name="R1" unitsValue="newton-meter" plotLabel="" id="35" />
<Component name="R2" unitsValue="newton-meter" plotLabel="" id="36" />
</Entity>
<Entity name="Brake.Locked_Spring_Moment" entity="Brake.Locked_Spring_Moment" entType="Request">
<Component name="L1" unitsValue="newton-meter" plotLabel="" id="37" />
<Component name="L2" unitsValue="newton-meter" plotLabel="" id="38" />
<Component name="R1" unitsValue="newton-meter" plotLabel="" id="39" />
<Component name="R2" unitsValue="newton-meter" plotLabel="" id="40" />
</Entity>
<Entity name="Brake.Locked_Switch" entity="Brake.Locked_Switch" entType="Request">
<Component name="L1" unitsValue="" plotLabel="Switch State" id="41" />
<Component name="L2" unitsValue="" plotLabel="Switch State" id="42" />
<Component name="R1" unitsValue="" plotLabel="Switch State" id="43" />
<Component name="R2" unitsValue="" plotLabel="Switch State" id="44" />
</Entity>
<Entity name="Brake.Lockup_Rotation" entity="Brake.Lockup_Rotation" entType="Request">
<Component name="L1" unitsValue="radian" plotLabel="" id="45" />
<Component name="L2" unitsValue="radian" plotLabel="" id="46" />
<Component name="R1" unitsValue="radian" plotLabel="" id="47" />
<Component name="R2" unitsValue="radian" plotLabel="" id="48" />
</Entity>
<Entity name="Brake_System" entity="Brake_System" entType="Request">
<Component name="Hill_Holder_Activity" unitsValue="" plotLabel="(-)" id="49" />
<Component name="ESP_Activity" unitsValue="" plotLabel="(-)" id="50" />
<Component name="Front_Master_Cylinder_Pressure" unitsValue="newton/meter**2" plotLabel="" id="51" />
<Component name="Rear_Master_Cylinder_Pressure" unitsValue="newton/meter**2" plotLabel="" id="52" />
<Component name="Front_Line_Pressure" unitsValue="newton/meter**2" plotLabel="" id="53" />
<Component name="Rear_Line_Pressure" unitsValue="newton/meter**2" plotLabel="" id="54" />
<Component name="Front_Master_Cylinder_Pressure_Internal" unitsValue="newton/meter**2" plotLabel="" id="55" />
<Component name="Rear_Master_Cylinder_Pressure_Internal" unitsValue="newton/meter**2" plotLabel="" id="56" />
</Entity>
<Entity name="Damper.Force_At_Damper" entity="Damper.Force_At_Damper" entType="Request">
<Component name="L1" unitsValue="newton" plotLabel="" id="57" />
<Component name="L2" unitsValue="newton" plotLabel="" id="58" />
<Component name="R1" unitsValue="newton" plotLabel="" id="59" />
<Component name="R2" unitsValue="newton" plotLabel="" id="60" />
</Entity>
<Entity name="Damper.Force_At_Wheel" entity="Damper.Force_At_Wheel" entType="Request">
<Component name="L1" unitsValue="newton" plotLabel="" id="61" />
<Component name="L2" unitsValue="newton" plotLabel="" id="62" />
<Component name="R1" unitsValue="newton" plotLabel="" id="63" />
<Component name="R2" unitsValue="newton" plotLabel="" id="64" />
</Entity>
<Entity name="Damper.Jounce" entity="Damper.Jounce" entType="Request">
<Component name="L1" unitsValue="meter" plotLabel="" id="65" />
<Component name="L2" unitsValue="meter" plotLabel="" id="66" />
<Component name="R1" unitsValue="meter" plotLabel="" id="67" />
<Component name="R2" unitsValue="meter" plotLabel="" id="68" />
</Entity>
<Entity name="Damper.Jounce_Acceleration" entity="Damper.Jounce_Acceleration" entType="Request">
<Component name="L1" unitsValue="meter/second**2" plotLabel="" id="69" />
<Component name="L2" unitsValue="meter/second**2" plotLabel="" id="70" />
<Component name="R1" unitsValue="meter/second**2" plotLabel="" id="71" />
<Component name="R2" unitsValue="meter/second**2" plotLabel="" id="72" />
</Entity>
<Entity name="Damper.Jounce_Rate" entity="Damper.Jounce_Rate" entType="Request">
<Component name="L1" unitsValue="meter/second" plotLabel="" id="73" />
<Component name="L2" unitsValue="meter/second" plotLabel="" id="74" />
<Component name="R1" unitsValue="meter/second" plotLabel="" id="75" />
<Component name="R2" unitsValue="meter/second" plotLabel="" id="76" />
</Entity>
<Entity name="FrontLeft" entity="FrontLeft" entType="Request">
<Component name="DX" unitsValue="meter" plotLabel="" id="77" />
<Component name="DY" unitsValue="meter" plotLabel="" id="78" />
<Component name="DZ" unitsValue="meter" plotLabel="" id="79" />
<Component name="VX" unitsValue="meter/second" plotLabel="" id="80" />
<Component name="VY" unitsValue="meter/second" plotLabel="" id="81" />
<Component name="VZ" unitsValue="meter/second" plotLabel="" id="82" />
<Component name="FX" unitsValue="Newton" plotLabel="" id="83" />
<Component name="FY" unitsValue="Newton" plotLabel="" id="84" />
<Component name="FZ" unitsValue="Newton" plotLabel="" id="85" />
</Entity>
<Entity name="FrontRight" entity="FrontRight" entType="Request">
<Component name="DX" unitsValue="meter" plotLabel="" id="86" />
<Component name="DY" unitsValue="meter" plotLabel="" id="87" />
<Component name="DZ" unitsValue="meter" plotLabel="" id="88" />
<Component name="VX" unitsValue="meter/second" plotLabel="" id="89" />
<Component name="VY" unitsValue="meter/second" plotLabel="" id="90" />
<Component name="VZ" unitsValue="meter/second" plotLabel="" id="91" />
<Component name="FX" unitsValue="Newton" plotLabel="" id="92" />
<Component name="FY" unitsValue="Newton" plotLabel="" id="93" />
<Component name="FZ" unitsValue="Newton" plotLabel="" id="94" />
</Entity>
<Entity name="Gyro" entity="Gyro" entType="Request">
<Component name="Driver_X" unitsValue="meter" plotLabel="" id="95" />
<Component name="Driver_Z" unitsValue="meter" plotLabel="" id="96" />
<Component name="gyro_ACCX" unitsValue="meter/second**2" plotLabel="" id="97" />
<Component name="gyro_ACCY" unitsValue="meter/second**2" plotLabel="" id="98" />
<Component name="gyro_VX" unitsValue="meter/second" plotLabel="" id="99" />
<Component name="gyro_X" unitsValue="meter" plotLabel="" id="100" />
<Component name="gyro_Y" unitsValue="meter" plotLabel="" id="101" />
<Component name="sensor_1_Z" unitsValue="meter" plotLabel="" id="102" />
<Component name="sensor_2_Z" unitsValue="meter" plotLabel="" id="103" />
<Component name="sensor_3_Z" unitsValue="meter" plotLabel="" id="104" />
</Entity>
<Entity name="Jounce_Bumper.Force_At_Bumper" entity="Jounce_Bumper.Force_At_Bumper" entType="Request">
<Component name="L1" unitsValue="newton" plotLabel="" id="105" />
<Component name="L2" unitsValue="newton" plotLabel="" id="106" />
<Component name="R1" unitsValue="newton" plotLabel="" id="107" />
<Component name="R2" unitsValue="newton" plotLabel="" id="108" />
</Entity>
<Entity name="Jounce_Bumper.Force_At_Wheel" entity="Jounce_Bumper.Force_At_Wheel" entType="Request">
<Component name="L1" unitsValue="newton" plotLabel="" id="109" />
<Component name="L2" unitsValue="newton" plotLabel="" id="110" />
<Component name="R1" unitsValue="newton" plotLabel="" id="111" />
<Component name="R2" unitsValue="newton" plotLabel="" id="112" />
</Entity>
<Entity name="Jounce_Bumper.Jounce" entity="Jounce_Bumper.Jounce" entType="Request">
<Component name="L1" unitsValue="meter" plotLabel="" id="113" />
<Component name="L2" unitsValue="meter" plotLabel="" id="114" />
<Component name="R1" unitsValue="meter" plotLabel="" id="115" />
<Component name="R2" unitsValue="meter" plotLabel="" id="116" />
</Entity>
<Entity name="Jounce_Bumper.Jounce_Rate" entity="Jounce_Bumper.Jounce_Rate" entType="Request">
<Component name="L1" unitsValue="meter/second" plotLabel="" id="117" />
<Component name="L2" unitsValue="meter/second" plotLabel="" id="118" />
<Component name="R1" unitsValue="meter/second" plotLabel="" id="119" />
<Component name="R2" unitsValue="meter/second" plotLabel="" id="120" />
</Entity>
<Entity name="Pushrod_Load" entity="Pushrod_Load" entType="Request">
<Component name="R1" unitsValue="Newton" plotLabel="" id="121" />
<Component name="R2" unitsValue="Newton" plotLabel="" id="122" />
</Entity>
<Entity name="RearLeft" entity="RearLeft" entType="Request">
<Component name="DX" unitsValue="meter" plotLabel="" id="123" />
<Component name="DY" unitsValue="meter" plotLabel="" id="124" />
<Component name="DZ" unitsValue="meter" plotLabel="" id="125" />
<Component name="VX" unitsValue="meter/second" plotLabel="" id="126" />
<Component name="VY" unitsValue="meter/second" plotLabel="" id="127" />
<Component name="VZ" unitsValue="meter/second" plotLabel="" id="128" />
<Component name="FX" unitsValue="Newton" plotLabel="" id="129" />
<Component name="FY" unitsValue="Newton" plotLabel="" id="130" />
<Component name="FZ" unitsValue="Newton" plotLabel="" id="131" />
</Entity>
<Entity name="RearRight" entity="RearRight" entType="Request">
<Component name="DX" unitsValue="meter" plotLabel="" id="132" />
<Component name="DY" unitsValue="meter" plotLabel="" id="133" />
<Component name="DZ" unitsValue="meter" plotLabel="" id="134" />
<Component name="VX" unitsValue="meter/second" plotLabel="" id="135" />
<Component name="VY" unitsValue="meter/second" plotLabel="" id="136" />
<Component name="VZ" unitsValue="meter/second" plotLabel="" id="137" />
<Component name="FX" unitsValue="Newton" plotLabel="" id="138" />
<Component name="FY" unitsValue="Newton" plotLabel="" id="139" />
<Component name="FZ" unitsValue="Newton" plotLabel="" id="140" />
</Entity>
<Entity name="Rebound_Bumper.Force_At_Bumper" entity="Rebound_Bumper.Force_At_Bumper" entType="Request">
<Component name="L1" unitsValue="newton" plotLabel="" id="141" />
<Component name="L2" unitsValue="newton" plotLabel="" id="142" />
<Component name="R1" unitsValue="newton" plotLabel="" id="143" />
<Component name="R2" unitsValue="newton" plotLabel="" id="144" />
</Entity>
<Entity name="Rebound_Bumper.Force_At_Wheel" entity="Rebound_Bumper.Force_At_Wheel" entType="Request">
<Component name="L1" unitsValue="newton" plotLabel="" id="145" />
<Component name="L2" unitsValue="newton" plotLabel="" id="146" />
<Component name="R1" unitsValue="newton" plotLabel="" id="147" />
<Component name="R2" unitsValue="newton" plotLabel="" id="148" />
</Entity>
<Entity name="Rebound_Bumper.Jounce" entity="Rebound_Bumper.Jounce" entType="Request">
<Component name="L1" unitsValue="meter" plotLabel="" id="149" />
<Component name="L2" unitsValue="meter" plotLabel="" id="150" />
<Component name="R1" unitsValue="meter" plotLabel="" id="151" />
<Component name="R2" unitsValue="meter" plotLabel="" id="152" />
</Entity>
<Entity name="Rebound_Bumper.Jounce_Rate" entity="Rebound_Bumper.Jounce_Rate" entType="Request">
<Component name="L1" unitsValue="meter/second" plotLabel="" id="153" />
<Component name="L2" unitsValue="meter/second" plotLabel="" id="154" />
<Component name="R1" unitsValue="meter/second" plotLabel="" id="155" />
<Component name="R2" unitsValue="meter/second" plotLabel="" id="156" />
</Entity>
<Entity name="Road.Contact_Flag" entity="Road.Contact_Flag" entType="Request">
<Component name="L1" unitsValue="" plotLabel="None(-)" id="157" />
<Component name="L2" unitsValue="" plotLabel="None(-)" id="158" />
<Component name="R1" unitsValue="" plotLabel="None(-)" id="159" />
<Component name="R2" unitsValue="" plotLabel="None(-)" id="160" />
</Entity>
<Entity name="Road.Contact_Patch_Global_X" entity="Road.Contact_Patch_Global_X" entType="Request">
<Component name="L1" unitsValue="meter" plotLabel="" id="161" />
<Component name="L2" unitsValue="meter" plotLabel="" id="162" />
<Component name="R1" unitsValue="meter" plotLabel="" id="163" />
<Component name="R2" unitsValue="meter" plotLabel="" id="164" />
</Entity>
<Entity name="Road.Contact_Patch_Global_Y" entity="Road.Contact_Patch_Global_Y" entType="Request">
<Component name="L1" unitsValue="meter" plotLabel="" id="165" />
<Component name="L2" unitsValue="meter" plotLabel="" id="166" />
<Component name="R1" unitsValue="meter" plotLabel="" id="167" />
<Component name="R2" unitsValue="meter" plotLabel="" id="168" />
</Entity>
<Entity name="Road.Contact_Patch_Global_Z" entity="Road.Contact_Patch_Global_Z" entType="Request">
<Component name="L1" unitsValue="meter" plotLabel="" id="169" />
<Component name="L2" unitsValue="meter" plotLabel="" id="170" />
<Component name="R1" unitsValue="meter" plotLabel="" id="171" />
<Component name="R2" unitsValue="meter" plotLabel="" id="172" />
</Entity>
<Entity name="Road.Off_Road_Flag" entity="Road.Off_Road_Flag" entType="Request">
<Component name="L1" unitsValue="" plotLabel="None(-)" id="173" />
<Component name="L2" unitsValue="" plotLabel="None(-)" id="174" />
<Component name="R1" unitsValue="" plotLabel="None(-)" id="175" />
<Component name="R2" unitsValue="" plotLabel="None(-)" id="176" />
</Entity>
<Entity name="Road_Material" entity="Road_Material" entType="Request">
<Component name="front_left_tire" unitsValue="" plotLabel="material id (-)" id="177" />
<Component name="front_right_tire" unitsValue="" plotLabel="material id (-)" id="178" />
<Component name="rear_left_tire" unitsValue="" plotLabel="material id (-)" id="179" />
<Component name="rear_right_tire" unitsValue="" plotLabel="material id (-)" id="180" />
</Entity>
<Entity name="Sensor" entity="Sensor" entType="Request">
<Component name="AccX_gyro" unitsValue="meter/second**2" plotLabel="" id="181" />
<Component name="AccY_gyro" unitsValue="meter/second**2" plotLabel="" id="182" />
<Component name="Ax" unitsValue="meter/second**2" plotLabel="" id="183" />
<Component name="Ax_Without_Gravity" unitsValue="meter/second**2" plotLabel="" id="184" />
<Component name="Ay" unitsValue="meter/second**2" plotLabel="" id="185" />
<Component name="Ay_Without_Gravity" unitsValue="meter/second**2" plotLabel="" id="186" />
<Component name="Az" unitsValue="meter/second**2" plotLabel="" id="187" />
<Component name="Az_Without_Gravity" unitsValue="meter/second**2" plotLabel="" id="188" />
<Component name="Global_X" unitsValue="meter" plotLabel="" id="189" />
<Component name="Global_Y" unitsValue="meter" plotLabel="" id="190" />
<Component name="Global_Z" unitsValue="meter" plotLabel="" id="191" />
<Component name="Vx" unitsValue="meter/second" plotLabel="" id="192" />
<Component name="Vx_gyro" unitsValue="meter/second" plotLabel="" id="193" />
<Component name="Vy" unitsValue="meter/second" plotLabel="" id="194" />
<Component name="Vz" unitsValue="meter/second" plotLabel="" id="195" />
<Component name="YawRate_gyro" unitsValue="radian/second" plotLabel="" id="196" />
</Entity>
<Entity name="Spring.Aggregate_Force_At_Wheel" entity="Spring.Aggregate_Force_At_Wheel" entType="Request">
<Component name="L1" unitsValue="newton" plotLabel="" id="197" />
<Component name="L2" unitsValue="newton" plotLabel="" id="198" />
<Component name="R1" unitsValue="newton" plotLabel="" id="199" />
<Component name="R2" unitsValue="newton" plotLabel="" id="200" />
</Entity>
<Entity name="Spring.Force_At_Spring" entity="Spring.Force_At_Spring" entType="Request">
<Component name="L1" unitsValue="newton" plotLabel="" id="201" />
<Component name="L2" unitsValue="newton" plotLabel="" id="202" />
<Component name="R1" unitsValue="newton" plotLabel="" id="203" />
<Component name="R2" unitsValue="newton" plotLabel="" id="204" />
</Entity>
<Entity name="Spring.Force_At_Wheel" entity="Spring.Force_At_Wheel" entType="Request">
<Component name="L1" unitsValue="newton" plotLabel="" id="205" />
<Component name="L2" unitsValue="newton" plotLabel="" id="206" />
<Component name="R1" unitsValue="newton" plotLabel="" id="207" />
<Component name="R2" unitsValue="newton" plotLabel="" id="208" />
</Entity>
<Entity name="Spring.Force_Aux_At_Wheel" entity="Spring.Force_Aux_At_Wheel" entType="Request">
<Component name="L1" unitsValue="newton" plotLabel="" id="209" />
<Component name="L2" unitsValue="newton" plotLabel="" id="210" />
<Component name="R1" unitsValue="newton" plotLabel="" id="211" />
<Component name="R2" unitsValue="newton" plotLabel="" id="212" />
</Entity>
<Entity name="Spring.Jounce" entity="Spring.Jounce" entType="Request">
<Component name="L1" unitsValue="meter" plotLabel="" id="213" />
<Component name="L2" unitsValue="meter" plotLabel="" id="214" />
<Component name="R1" unitsValue="meter" plotLabel="" id="215" />
<Component name="R2" unitsValue="meter" plotLabel="" id="216" />
</Entity>
<Entity name="Spring.Jounce_Acceleration" entity="Spring.Jounce_Acceleration" entType="Request">
<Component name="L1" unitsValue="meter/second**2" plotLabel="" id="217" />
<Component name="L2" unitsValue="meter/second**2" plotLabel="" id="218" />
<Component name="R1" unitsValue="meter/second**2" plotLabel="" id="219" />
<Component name="R2" unitsValue="meter/second**2" plotLabel="" id="220" />
</Entity>
<Entity name="Spring.Jounce_Rate" entity="Spring.Jounce_Rate" entType="Request">
<Component name="L1" unitsValue="meter/second" plotLabel="" id="221" />
<Component name="L2" unitsValue="meter/second" plotLabel="" id="222" />
<Component name="R1" unitsValue="meter/second" plotLabel="" id="223" />
<Component name="R2" unitsValue="meter/second" plotLabel="" id="224" />
</Entity>
<Entity name="Spring.PID_CW_At_Spring" entity="Spring.PID_CW_At_Spring" entType="Request">
<Component name="L1" unitsValue="newton" plotLabel="" id="225" />
<Component name="L2" unitsValue="newton" plotLabel="" id="226" />
<Component name="R1" unitsValue="newton" plotLabel="" id="227" />
<Component name="R2" unitsValue="newton" plotLabel="" id="228" />
</Entity>
<Entity name="Spring.PID_PH_At_Spring" entity="Spring.PID_PH_At_Spring" entType="Request">
<Component name="L1" unitsValue="newton" plotLabel="" id="229" />
<Component name="L2" unitsValue="newton" plotLabel="" id="230" />
<Component name="R1" unitsValue="newton" plotLabel="" id="231" />
<Component name="R2" unitsValue="newton" plotLabel="" id="232" />
</Entity>
<Entity name="Spring.PID_RH_At_Spring" entity="Spring.PID_RH_At_Spring" entType="Request">
<Component name="L1" unitsValue="newton" plotLabel="" id="233" />
<Component name="L2" unitsValue="newton" plotLabel="" id="234" />
<Component name="R1" unitsValue="newton" plotLabel="" id="235" />
<Component name="R2" unitsValue="newton" plotLabel="" id="236" />
</Entity>
<Entity name="Steering_System" entity="Steering_System" entType="Request">
<Component name="DriveSim_Steering_Feedback_Torque" unitsValue="newton-meter" plotLabel="" id="237" />
<Component name="Rack_displacement" unitsValue="meter" plotLabel="" id="238" />
<Component name="Rack_Force" unitsValue="newton" plotLabel="" id="239" />
<Component name="Steering_column_deformation" unitsValue="radian" plotLabel="" id="240" />
<Component name="Steering_Wheel_Torque" unitsValue="newton-meter" plotLabel="" id="241" />
</Entity>
<Entity name="Steering_System.TieRod_Force_Left" entity="Steering_System.TieRod_Force_Left" entType="Request">
<Component name="X" unitsValue="newton" plotLabel="" id="242" />
<Component name="Y" unitsValue="newton" plotLabel="" id="243" />
<Component name="Z" unitsValue="newton" plotLabel="" id="244" />
</Entity>
<Entity name="Steering_System.TieRod_Force_Right" entity="Steering_System.TieRod_Force_Right" entType="Request">
<Component name="X" unitsValue="newton" plotLabel="" id="245" />
<Component name="Y" unitsValue="newton" plotLabel="" id="246" />
<Component name="Z" unitsValue="newton" plotLabel="" id="247" />
</Entity>
<Entity name="Suspension.Auxiliary_Roll_Force" entity="Suspension.Auxiliary_Roll_Force" entType="Request">
<Component name="SUSP_L1" unitsValue="newton" plotLabel="" id="248" />
<Component name="SUSP_L2" unitsValue="newton" plotLabel="" id="249" />
<Component name="SUSP_R1" unitsValue="newton" plotLabel="" id="250" />
<Component name="SUSP_R2" unitsValue="newton" plotLabel="" id="251" />
</Entity>
<Entity name="Suspension.Auxiliary_Roll_Force_at_element" entity="Suspension.Auxiliary_Roll_Force_at_element" entType="Request">
<Component name="SUSP1" unitsValue="newton-meter" plotLabel="" id="252" />
<Component name="SUSP2" unitsValue="newton-meter" plotLabel="" id="253" />
</Entity>
<Entity name="Suspension.Auxiliary_Roll_deformation_at_element" entity="Suspension.Auxiliary_Roll_deformation_at_element" entType="Request">
<Component name="SUSP1" unitsValue="radian" plotLabel="" id="254" />
<Component name="SUSP2" unitsValue="radian" plotLabel="" id="255" />
</Entity>
<Entity name="Suspension.Inst_Stiff_Deflection" entity="Suspension.Inst_Stiff_Deflection" entType="Request">
<Component name="front_left" unitsValue="meter" plotLabel="" id="256" />
<Component name="front_right" unitsValue="meter" plotLabel="" id="257" />
<Component name="rear_left" unitsValue="meter" plotLabel="" id="258" />
<Component name="rear_right" unitsValue="meter" plotLabel="" id="259" />
</Entity>
<Entity name="Suspension.Inst_Stiff_Force" entity="Suspension.Inst_Stiff_Force" entType="Request">
<Component name="front_left" unitsValue="Newton" plotLabel="" id="260" />
<Component name="front_right" unitsValue="Newton" plotLabel="" id="261" />
<Component name="rear_left" unitsValue="Newton" plotLabel="" id="262" />
<Component name="rear_right" unitsValue="Newton" plotLabel="" id="263" />
</Entity>
<Entity name="Suspension.Jounce" entity="Suspension.Jounce" entType="Request">
<Component name="L1" unitsValue="meter" plotLabel="" id="264" />
<Component name="L2" unitsValue="meter" plotLabel="" id="265" />
<Component name="R1" unitsValue="meter" plotLabel="" id="266" />
<Component name="R2" unitsValue="meter" plotLabel="" id="267" />
</Entity>
<Entity name="Suspension.Jounce_Acceleration" entity="Suspension.Jounce_Acceleration" entType="Request">
<Component name="L1" unitsValue="meter/second**2" plotLabel="" id="268" />
<Component name="L2" unitsValue="meter/second**2" plotLabel="" id="269" />
<Component name="R1" unitsValue="meter/second**2" plotLabel="" id="270" />
<Component name="R2" unitsValue="meter/second**2" plotLabel="" id="271" />
</Entity>
<Entity name="Suspension.Jounce_Rate" entity="Suspension.Jounce_Rate" entType="Request">
<Component name="L1" unitsValue="meter/second" plotLabel="" id="272" />
<Component name="L2" unitsValue="meter/second" plotLabel="" id="273" />
<Component name="R1" unitsValue="meter/second" plotLabel="" id="274" />
<Component name="R2" unitsValue="meter/second" plotLabel="" id="275" />
</Entity>
<Entity name="Suspension.Kingpin_Moment" entity="Suspension.Kingpin_Moment" entType="Request">
<Component name="SUSP1" unitsValue="newton-meter" plotLabel="" id="276" />
</Entity>
<Entity name="Suspension.Roll" entity="Suspension.Roll" entType="Request">
<Component name="SUSP1" unitsValue="radian" plotLabel="" id="277" />
<Component name="SUSP2" unitsValue="radian" plotLabel="" id="278" />
</Entity>
<Entity name="Suspension.Roll_Center_Height" entity="Suspension.Roll_Center_Height" entType="Request">
<Component name="front" unitsValue="meter" plotLabel="" id="279" />
<Component name="rear" unitsValue="meter" plotLabel="" id="280" />
</Entity>
<Entity name="Suspension.Roll_Center_Lateral_Displacement" entity="Suspension.Roll_Center_Lateral_Displacement" entType="Request">
<Component name="front" unitsValue="meter" plotLabel="" id="281" />
<Component name="rear" unitsValue="meter" plotLabel="" id="282" />
</Entity>
<Entity name="Suspension.Steering_Instant_Axis_Rotation" entity="Suspension.Steering_Instant_Axis_Rotation" entType="Request">
<Component name="L1" unitsValue="radian" plotLabel="" id="283" />
<Component name="R1" unitsValue="radian" plotLabel="" id="284" />
</Entity>
<Entity name="Suspension.base_acceleration" entity="Suspension.base_acceleration" entType="Request">
<Component name="L1" unitsValue="meter/second**2" plotLabel="" id="285" />
<Component name="L2" unitsValue="meter/second**2" plotLabel="" id="286" />
<Component name="R1" unitsValue="meter/second**2" plotLabel="" id="287" />
<Component name="R2" unitsValue="meter/second**2" plotLabel="" id="288" />
</Entity>
<Entity name="Suspension.base_deformation" entity="Suspension.base_deformation" entType="Request">
<Component name="L1" unitsValue="meter" plotLabel="" id="289" />
<Component name="L2" unitsValue="meter" plotLabel="" id="290" />
<Component name="R1" unitsValue="meter" plotLabel="" id="291" />
<Component name="R2" unitsValue="meter" plotLabel="" id="292" />
</Entity>
<Entity name="Suspension.base_velocity" entity="Suspension.base_velocity" entType="Request">
<Component name="L1" unitsValue="meter/second" plotLabel="" id="293" />
<Component name="L2" unitsValue="meter/second" plotLabel="" id="294" />
<Component name="R1" unitsValue="meter/second" plotLabel="" id="295" />
<Component name="R2" unitsValue="meter/second" plotLabel="" id="296" />
</Entity>
<Entity name="System" entity="System" entType="Request">
<Component name="Angular_Acceleration_Norm" unitsValue="radian/second**2" plotLabel="" id="297" />
<Component name="Angular_Speed_Norm" unitsValue="radian/second" plotLabel="" id="298" />
<Component name="Time" unitsValue="second" plotLabel="" id="299" />
<Component name="Translational_Acceleration_Norm" unitsValue="meter/second**2" plotLabel="" id="300" />
<Component name="Translational_Speed_Norm" unitsValue="meter/second" plotLabel="" id="301" />
<Component name="Solver_Status" unitsValue="" plotLabel="(-)" id="302" />
</Entity>
<Entity name="System_Mass_Center" entity="System_Mass_Center" entType="Request">
<Component name="Global_Ax" unitsValue="" plotLabel="Acceleration (g)" id="303" />
<Component name="Global_Ay" unitsValue="" plotLabel="Acceleration (g)" id="304" />
<Component name="Global_Az" unitsValue="" plotLabel="Acceleration (g)" id="305" />
<Component name="Global_Vx" unitsValue="" plotLabel="Velocity (km/h)" id="306" />
<Component name="Global_Vy" unitsValue="" plotLabel="Velocity (km/h)" id="307" />
<Component name="Global_Vz" unitsValue="" plotLabel="Velocity (km/h)" id="308" />
<Component name="Global_X" unitsValue="meter" plotLabel="" id="309" />
<Component name="Global_Y" unitsValue="meter" plotLabel="" id="310" />
<Component name="Global_Z" unitsValue="meter" plotLabel="" id="311" />
<Component name="Normal_Acceleration" unitsValue="" plotLabel="Acceleration (g)" id="312" />
<Component name="Path_Curvature" unitsValue="" plotLabel="Curvature (1/m)" id="313" />
<Component name="Speed" unitsValue="" plotLabel="Velocity (km/h)" id="314" />
<Component name="Tangential_Acceleration" unitsValue="" plotLabel="Acceleration (g)" id="315" />
</Entity>
<Entity name="Tire.Actual_Tread_Speed" entity="Tire.Actual_Tread_Speed" entType="Request">
<Component name="L1" unitsValue="" plotLabel="Velocity (km/h)" id="316" />
<Component name="L2" unitsValue="" plotLabel="Velocity (km/h)" id="317" />
<Component name="R1" unitsValue="" plotLabel="Velocity (km/h)" id="318" />
<Component name="R2" unitsValue="" plotLabel="Velocity (km/h)" id="319" />
</Entity>
<Entity name="Tire.Contact_Patch_Global_X" entity="Tire.Contact_Patch_Global_X" entType="Request">
<Component name="L1" unitsValue="meter" plotLabel="" id="320" />
<Component name="L2" unitsValue="meter" plotLabel="" id="321" />
<Component name="R1" unitsValue="meter" plotLabel="" id="322" />
<Component name="R2" unitsValue="meter" plotLabel="" id="323" />
</Entity>
<Entity name="Tire.Contact_Patch_Global_Y" entity="Tire.Contact_Patch_Global_Y" entType="Request">
<Component name="L1" unitsValue="meter" plotLabel="" id="324" />
<Component name="L2" unitsValue="meter" plotLabel="" id="325" />
<Component name="R1" unitsValue="meter" plotLabel="" id="326" />
<Component name="R2" unitsValue="meter" plotLabel="" id="327" />
</Entity>
<Entity name="Tire.Contact_Patch_Global_Z" entity="Tire.Contact_Patch_Global_Z" entType="Request">
<Component name="L1" unitsValue="meter" plotLabel="" id="328" />
<Component name="L2" unitsValue="meter" plotLabel="" id="329" />
<Component name="R1" unitsValue="meter" plotLabel="" id="330" />
<Component name="R2" unitsValue="meter" plotLabel="" id="331" />
</Entity>
<Entity name="Tire.Contact_Patch_Normal_X" entity="Tire.Contact_Patch_Normal_X" entType="Request">
<Component name="L1" unitsValue="" plotLabel="(Nx)" id="332" />
<Component name="L2" unitsValue="" plotLabel="(Nx)" id="333" />
<Component name="R1" unitsValue="" plotLabel="(Nx)" id="334" />
<Component name="R2" unitsValue="" plotLabel="(Nx)" id="335" />
</Entity>
<Entity name="Tire.Contact_Patch_Normal_Y" entity="Tire.Contact_Patch_Normal_Y" entType="Request">
<Component name="L1" unitsValue="" plotLabel="(Ny)" id="336" />
<Component name="L2" unitsValue="" plotLabel="(Ny)" id="337" />
<Component name="R1" unitsValue="" plotLabel="(Ny)" id="338" />
<Component name="R2" unitsValue="" plotLabel="(Ny)" id="339" />
</Entity>
<Entity name="Tire.Contact_Patch_Normal_Z" entity="Tire.Contact_Patch_Normal_Z" entType="Request">
<Component name="L1" unitsValue="" plotLabel="(Nz)" id="340" />
<Component name="L2" unitsValue="" plotLabel="(Nz)" id="341" />
<Component name="R1" unitsValue="" plotLabel="(Nz)" id="342" />
<Component name="R2" unitsValue="" plotLabel="(Nz)" id="343" />
</Entity>
<Entity name="Tire.Effective_Closing_Speed" entity="Tire.Effective_Closing_Speed" entType="Request">
<Component name="L1" unitsValue="meter/second" plotLabel="" id="344" />
<Component name="L2" unitsValue="meter/second" plotLabel="" id="345" />
<Component name="R1" unitsValue="meter/second" plotLabel="" id="346" />
<Component name="R2" unitsValue="meter/second" plotLabel="" id="347" />
</Entity>
<Entity name="Tire.Effective_Penetration" entity="Tire.Effective_Penetration" entType="Request">
<Component name="L1" unitsValue="meter" plotLabel="" id="348" />
<Component name="L2" unitsValue="meter" plotLabel="" id="349" />
<Component name="R1" unitsValue="meter" plotLabel="" id="350" />
<Component name="R2" unitsValue="meter" plotLabel="" id="351" />
</Entity>
<Entity name="Tire.Effective_Rolling_Radius" entity="Tire.Effective_Rolling_Radius" entType="Request">
<Component name="L1" unitsValue="meter" plotLabel="" id="352" />
<Component name="L2" unitsValue="meter" plotLabel="" id="353" />
<Component name="R1" unitsValue="meter" plotLabel="" id="354" />
<Component name="R2" unitsValue="meter" plotLabel="" id="355" />
</Entity>
<Entity name="Tire.Equivalent_Tread_Speed" entity="Tire.Equivalent_Tread_Speed" entType="Request">
<Component name="L1" unitsValue="" plotLabel="Velocity (km/h)" id="356" />
<Component name="L2" unitsValue="" plotLabel="Velocity (km/h)" id="357" />
<Component name="R1" unitsValue="" plotLabel="Velocity (km/h)" id="358" />
<Component name="R2" unitsValue="" plotLabel="Velocity (km/h)" id="359" />
</Entity>
<Entity name="Tire.External_Friction_Scale_Factor" entity="Tire.External_Friction_Scale_Factor" entType="Request">
<Component name="L1" unitsValue="" plotLabel="Friction Coefficient" id="360" />
<Component name="L2" unitsValue="" plotLabel="Friction Coefficient" id="361" />
<Component name="R1" unitsValue="" plotLabel="Friction Coefficient" id="362" />
<Component name="R2" unitsValue="" plotLabel="Friction Coefficient" id="363" />
</Entity>
<Entity name="Tire.Ground_Surface_Contact_Patch_Vx" entity="Tire.Ground_Surface_Contact_Patch_Vx" entType="Request">
<Component name="L1" unitsValue="" plotLabel="Velocity (km/h)" id="364" />
<Component name="L2" unitsValue="" plotLabel="Velocity (km/h)" id="365" />
<Component name="R1" unitsValue="" plotLabel="Velocity (km/h)" id="366" />
<Component name="R2" unitsValue="" plotLabel="Velocity (km/h)" id="367" />
</Entity>
<Entity name="Tire.Ground_Surface_Contact_Patch_Vy" entity="Tire.Ground_Surface_Contact_Patch_Vy" entType="Request">
<Component name="L1" unitsValue="" plotLabel="Velocity (km/h)" id="368" />
<Component name="L2" unitsValue="" plotLabel="Velocity (km/h)" id="369" />
<Component name="R1" unitsValue="" plotLabel="Velocity (km/h)" id="370" />
<Component name="R2" unitsValue="" plotLabel="Velocity (km/h)" id="371" />
</Entity>
<Entity name="Tire.Ground_Surface_Force_X" entity="Tire.Ground_Surface_Force_X" entType="Request">
<Component name="L1" unitsValue="newton" plotLabel="" id="372" />
<Component name="L2" unitsValue="newton" plotLabel="" id="373" />
<Component name="R1" unitsValue="newton" plotLabel="" id="374" />
<Component name="R2" unitsValue="newton" plotLabel="" id="375" />
</Entity>
<Entity name="Tire.Ground_Surface_Force_Y" entity="Tire.Ground_Surface_Force_Y" entType="Request">
<Component name="L1" unitsValue="newton" plotLabel="" id="376" />
<Component name="L2" unitsValue="newton" plotLabel="" id="377" />
<Component name="R1" unitsValue="newton" plotLabel="" id="378" />
<Component name="R2" unitsValue="newton" plotLabel="" id="379" />
</Entity>
<Entity name="Tire.Ground_Surface_Force_Z" entity="Tire.Ground_Surface_Force_Z" entType="Request">
<Component name="L1" unitsValue="newton" plotLabel="" id="380" />
<Component name="L2" unitsValue="newton" plotLabel="" id="381" />
<Component name="R1" unitsValue="newton" plotLabel="" id="382" />
<Component name="R2" unitsValue="newton" plotLabel="" id="383" />
</Entity>
<Entity name="Tire.Ground_Surface_Gyroscopic_Moment" entity="Tire.Ground_Surface_Gyroscopic_Moment" entType="Request">
<Component name="L1" unitsValue="newton-meter" plotLabel="" id="384" />
<Component name="L2" unitsValue="newton-meter" plotLabel="" id="385" />
<Component name="R1" unitsValue="newton-meter" plotLabel="" id="386" />
<Component name="R2" unitsValue="newton-meter" plotLabel="" id="387" />
</Entity>
<Entity name="Tire.Ground_Surface_Kappa_Fy" entity="Tire.Ground_Surface_Kappa_Fy" entType="Request">
<Component name="L1" unitsValue="newton" plotLabel="" id="388" />
<Component name="L2" unitsValue="newton" plotLabel="" id="389" />
<Component name="R1" unitsValue="newton" plotLabel="" id="390" />
<Component name="R2" unitsValue="newton" plotLabel="" id="391" />
</Entity>
<Entity name="Tire.Ground_Surface_Moment_X" entity="Tire.Ground_Surface_Moment_X" entType="Request">
<Component name="L1" unitsValue="newton-meter" plotLabel="" id="392" />
<Component name="L2" unitsValue="newton-meter" plotLabel="" id="393" />
<Component name="R1" unitsValue="newton-meter" plotLabel="" id="394" />
<Component name="R2" unitsValue="newton-meter" plotLabel="" id="395" />
</Entity>
<Entity name="Tire.Ground_Surface_Moment_Y" entity="Tire.Ground_Surface_Moment_Y" entType="Request">
<Component name="L1" unitsValue="newton-meter" plotLabel="" id="396" />
<Component name="L2" unitsValue="newton-meter" plotLabel="" id="397" />
<Component name="R1" unitsValue="newton-meter" plotLabel="" id="398" />
<Component name="R2" unitsValue="newton-meter" plotLabel="" id="399" />
</Entity>
<Entity name="Tire.Ground_Surface_Moment_Z" entity="Tire.Ground_Surface_Moment_Z" entType="Request">
<Component name="L1" unitsValue="newton-meter" plotLabel="" id="400" />
<Component name="L2" unitsValue="newton-meter" plotLabel="" id="401" />
<Component name="R1" unitsValue="newton-meter" plotLabel="" id="402" />
<Component name="R2" unitsValue="newton-meter" plotLabel="" id="403" />
</Entity>
<Entity name="Tire.Ground_Surface_Peak_Friction_X" entity="Tire.Ground_Surface_Peak_Friction_X" entType="Request">
<Component name="L1" unitsValue="" plotLabel="Friction Coefficient" id="404" />
<Component name="L2" unitsValue="" plotLabel="Friction Coefficient" id="405" />
<Component name="R1" unitsValue="" plotLabel="Friction Coefficient" id="406" />
<Component name="R2" unitsValue="" plotLabel="Friction Coefficient" id="407" />
</Entity>
<Entity name="Tire.Ground_Surface_Peak_Friction_Y" entity="Tire.Ground_Surface_Peak_Friction_Y" entType="Request">
<Component name="L1" unitsValue="" plotLabel="Friction Coefficient" id="408" />
<Component name="L2" unitsValue="" plotLabel="Friction Coefficient" id="409" />
<Component name="R1" unitsValue="" plotLabel="Friction Coefficient" id="410" />
<Component name="R2" unitsValue="" plotLabel="Friction Coefficient" id="411" />
</Entity>
<Entity name="Tire.Ground_Surface_Residual_Torque" entity="Tire.Ground_Surface_Residual_Torque" entType="Request">
<Component name="L1" unitsValue="newton-meter" plotLabel="" id="412" />
<Component name="L2" unitsValue="newton-meter" plotLabel="" id="413" />
<Component name="R1" unitsValue="newton-meter" plotLabel="" id="414" />
<Component name="R2" unitsValue="newton-meter" plotLabel="" id="415" />
</Entity>
<Entity name="Tire.Hub_Carrier_Force_Global_X" entity="Tire.Hub_Carrier_Force_Global_X" entType="Request">
<Component name="L1" unitsValue="newton" plotLabel="" id="416" />
<Component name="L2" unitsValue="newton" plotLabel="" id="417" />
<Component name="R1" unitsValue="newton" plotLabel="" id="418" />
<Component name="R2" unitsValue="newton" plotLabel="" id="419" />
</Entity>
<Entity name="Tire.Hub_Carrier_Force_Global_Y" entity="Tire.Hub_Carrier_Force_Global_Y" entType="Request">
<Component name="L1" unitsValue="newton" plotLabel="" id="420" />
<Component name="L2" unitsValue="newton" plotLabel="" id="421" />
<Component name="R1" unitsValue="newton" plotLabel="" id="422" />
<Component name="R2" unitsValue="newton" plotLabel="" id="423" />
</Entity>
<Entity name="Tire.Hub_Carrier_Force_Global_Z" entity="Tire.Hub_Carrier_Force_Global_Z" entType="Request">
<Component name="L1" unitsValue="newton" plotLabel="" id="424" />
<Component name="L2" unitsValue="newton" plotLabel="" id="425" />
<Component name="R1" unitsValue="newton" plotLabel="" id="426" />
<Component name="R2" unitsValue="newton" plotLabel="" id="427" />
</Entity>
<Entity name="Tire.Hub_Carrier_Force_Local_X" entity="Tire.Hub_Carrier_Force_Local_X" entType="Request">
<Component name="L1" unitsValue="newton" plotLabel="" id="428" />
<Component name="L2" unitsValue="newton" plotLabel="" id="429" />
<Component name="R1" unitsValue="newton" plotLabel="" id="430" />
<Component name="R2" unitsValue="newton" plotLabel="" id="431" />
</Entity>
<Entity name="Tire.Hub_Carrier_Force_Local_Y" entity="Tire.Hub_Carrier_Force_Local_Y" entType="Request">
<Component name="L1" unitsValue="newton" plotLabel="" id="432" />
<Component name="L2" unitsValue="newton" plotLabel="" id="433" />
<Component name="R1" unitsValue="newton" plotLabel="" id="434" />
<Component name="R2" unitsValue="newton" plotLabel="" id="435" />
</Entity>
<Entity name="Tire.Hub_Carrier_Force_Local_Z" entity="Tire.Hub_Carrier_Force_Local_Z" entType="Request">
<Component name="L1" unitsValue="newton" plotLabel="" id="436" />
<Component name="L2" unitsValue="newton" plotLabel="" id="437" />
<Component name="R1" unitsValue="newton" plotLabel="" id="438" />
<Component name="R2" unitsValue="newton" plotLabel="" id="439" />
</Entity>
<Entity name="Tire.Hub_Carrier_Moment_Global_X" entity="Tire.Hub_Carrier_Moment_Global_X" entType="Request">
<Component name="L1" unitsValue="newton-meter" plotLabel="" id="440" />
<Component name="L2" unitsValue="newton-meter" plotLabel="" id="441" />
<Component name="R1" unitsValue="newton-meter" plotLabel="" id="442" />
<Component name="R2" unitsValue="newton-meter" plotLabel="" id="443" />
</Entity>
<Entity name="Tire.Hub_Carrier_Moment_Global_Y" entity="Tire.Hub_Carrier_Moment_Global_Y" entType="Request">
<Component name="L1" unitsValue="newton-meter" plotLabel="" id="444" />
<Component name="L2" unitsValue="newton-meter" plotLabel="" id="445" />
<Component name="R1" unitsValue="newton-meter" plotLabel="" id="446" />
<Component name="R2" unitsValue="newton-meter" plotLabel="" id="447" />
</Entity>
<Entity name="Tire.Hub_Carrier_Moment_Global_Z" entity="Tire.Hub_Carrier_Moment_Global_Z" entType="Request">
<Component name="L1" unitsValue="newton-meter" plotLabel="" id="448" />
<Component name="L2" unitsValue="newton-meter" plotLabel="" id="449" />
<Component name="R1" unitsValue="newton-meter" plotLabel="" id="450" />
<Component name="R2" unitsValue="newton-meter" plotLabel="" id="451" />
</Entity>
<Entity name="Tire.Hub_Carrier_Moment_Local_X" entity="Tire.Hub_Carrier_Moment_Local_X" entType="Request">
<Component name="L1" unitsValue="newton-meter" plotLabel="" id="452" />
<Component name="L2" unitsValue="newton-meter" plotLabel="" id="453" />
<Component name="R1" unitsValue="newton-meter" plotLabel="" id="454" />
<Component name="R2" unitsValue="newton-meter" plotLabel="" id="455" />
</Entity>
<Entity name="Tire.Hub_Carrier_Moment_Local_Y" entity="Tire.Hub_Carrier_Moment_Local_Y" entType="Request">
<Component name="L1" unitsValue="newton-meter" plotLabel="" id="456" />
<Component name="L2" unitsValue="newton-meter" plotLabel="" id="457" />
<Component name="R1" unitsValue="newton-meter" plotLabel="" id="458" />
<Component name="R2" unitsValue="newton-meter" plotLabel="" id="459" />
</Entity>
<Entity name="Tire.Hub_Carrier_Moment_Local_Z" entity="Tire.Hub_Carrier_Moment_Local_Z" entType="Request">
<Component name="L1" unitsValue="newton-meter" plotLabel="" id="460" />
<Component name="L2" unitsValue="newton-meter" plotLabel="" id="461" />
<Component name="R1" unitsValue="newton-meter" plotLabel="" id="462" />
<Component name="R2" unitsValue="newton-meter" plotLabel="" id="463" />
</Entity>
<Entity name="Tire.Lateral_Relaxation_Length" entity="Tire.Lateral_Relaxation_Length" entType="Request">
<Component name="L1" unitsValue="meter" plotLabel="" id="464" />
<Component name="L2" unitsValue="meter" plotLabel="" id="465" />
<Component name="R1" unitsValue="meter" plotLabel="" id="466" />
<Component name="R2" unitsValue="meter" plotLabel="" id="467" />
</Entity>
<Entity name="Tire.Lateral_Slip_With_Lag" entity="Tire.Lateral_Slip_With_Lag" entType="Request">
<Component name="L1" unitsValue="radian" plotLabel="" id="468" />
<Component name="L2" unitsValue="radian" plotLabel="" id="469" />
<Component name="R1" unitsValue="radian" plotLabel="" id="470" />
<Component name="R2" unitsValue="radian" plotLabel="" id="471" />
</Entity>
<Entity name="Tire.Lateral_Slip_Without_Lag" entity="Tire.Lateral_Slip_Without_Lag" entType="Request">
<Component name="L1" unitsValue="radian" plotLabel="" id="472" />
<Component name="L2" unitsValue="radian" plotLabel="" id="473" />
<Component name="R1" unitsValue="radian" plotLabel="" id="474" />
<Component name="R2" unitsValue="radian" plotLabel="" id="475" />
</Entity>
<Entity name="Tire.Loaded_Radius" entity="Tire.Loaded_Radius" entType="Request">
<Component name="L1" unitsValue="meter" plotLabel="" id="476" />
<Component name="L2" unitsValue="meter" plotLabel="" id="477" />
<Component name="R1" unitsValue="meter" plotLabel="" id="478" />
<Component name="R2" unitsValue="meter" plotLabel="" id="479" />
</Entity>
<Entity name="Tire.Longitudinal_Relaxation_Length" entity="Tire.Longitudinal_Relaxation_Length" entType="Request">
<Component name="L1" unitsValue="meter" plotLabel="" id="480" />
<Component name="L2" unitsValue="meter" plotLabel="" id="481" />
<Component name="R1" unitsValue="meter" plotLabel="" id="482" />
<Component name="R2" unitsValue="meter" plotLabel="" id="483" />
</Entity>
<Entity name="Tire.Longitudinal_Slip_With_Lag" entity="Tire.Longitudinal_Slip_With_Lag" entType="Request">
<Component name="L1" unitsValue="" plotLabel="(Longitudinal Slip [-1 = lockup])" id="484" />
<Component name="L2" unitsValue="" plotLabel="(Longitudinal Slip [-1 = lockup])" id="485" />
<Component name="R1" unitsValue="" plotLabel="(Longitudinal Slip [-1 = lockup])" id="486" />
<Component name="R2" unitsValue="" plotLabel="(Longitudinal Slip [-1 = lockup])" id="487" />
</Entity>
<Entity name="Tire.Longitudinal_Slip_Without_Lag" entity="Tire.Longitudinal_Slip_Without_Lag" entType="Request">
<Component name="L1" unitsValue="" plotLabel="(Longitudinal Slip [-1 = lockup])" id="488" />
<Component name="L2" unitsValue="" plotLabel="(Longitudinal Slip [-1 = lockup])" id="489" />
<Component name="R1" unitsValue="" plotLabel="(Longitudinal Slip [-1 = lockup])" id="490" />
<Component name="R2" unitsValue="" plotLabel="(Longitudinal Slip [-1 = lockup])" id="491" />
</Entity>
<Entity name="Tire.Moment_Arm_Of_Fx" entity="Tire.Moment_Arm_Of_Fx" entType="Request">
<Component name="L1" unitsValue="meter" plotLabel="" id="492" />
<Component name="L2" unitsValue="meter" plotLabel="" id="493" />
<Component name="R1" unitsValue="meter" plotLabel="" id="494" />
<Component name="R2" unitsValue="meter" plotLabel="" id="495" />
</Entity>
<Entity name="Tire.Pneumatic_Trail" entity="Tire.Pneumatic_Trail" entType="Request">
<Component name="L1" unitsValue="meter" plotLabel="" id="496" />
<Component name="L2" unitsValue="meter" plotLabel="" id="497" />
<Component name="R1" unitsValue="meter" plotLabel="" id="498" />
<Component name="R2" unitsValue="meter" plotLabel="" id="499" />
</Entity>
<Entity name="Tire.Pressure" entity="Tire.Pressure" entType="Request">
<Component name="L1" unitsValue="" plotLabel="(Pressure)" id="500" />
<Component name="L2" unitsValue="" plotLabel="(Pressure)" id="501" />
<Component name="R1" unitsValue="" plotLabel="(Pressure)" id="502" />
<Component name="R2" unitsValue="" plotLabel="(Pressure)" id="503" />
</Entity>
<Entity name="Tire.Road_friction" entity="Tire.Road_friction" entType="Request">
<Component name="L1" unitsValue="" plotLabel="Friction Coefficient ( - )" id="504" />
<Component name="L2" unitsValue="" plotLabel="Friction Coefficient ( - )" id="505" />
<Component name="R1" unitsValue="" plotLabel="Friction Coefficient ( - )" id="506" />
<Component name="R2" unitsValue="" plotLabel="Friction Coefficient ( - )" id="507" />
</Entity>
<Entity name="Tire.Temperature_1" entity="Tire.Temperature_1" entType="Request">
<Component name="L1" unitsValue="" plotLabel="(Temperature)" id="508" />
<Component name="L2" unitsValue="" plotLabel="(Temperature)" id="509" />
<Component name="R1" unitsValue="" plotLabel="(Temperature)" id="510" />
<Component name="R2" unitsValue="" plotLabel="(Temperature)" id="511" />
</Entity>
<Entity name="Tire.Temperature_2" entity="Tire.Temperature_2" entType="Request">
<Component name="L1" unitsValue="" plotLabel="(Temperature)" id="512" />
<Component name="L2" unitsValue="" plotLabel="(Temperature)" id="513" />
<Component name="R1" unitsValue="" plotLabel="(Temperature)" id="514" />
<Component name="R2" unitsValue="" plotLabel="(Temperature)" id="515" />
</Entity>
<Entity name="Tire.Temperature_3" entity="Tire.Temperature_3" entType="Request">
<Component name="L1" unitsValue="" plotLabel="(Temperature)" id="516" />
<Component name="L2" unitsValue="" plotLabel="(Temperature)" id="517" />
<Component name="R1" unitsValue="" plotLabel="(Temperature)" id="518" />
<Component name="R2" unitsValue="" plotLabel="(Temperature)" id="519" />
</Entity>
<Entity name="Tire.Temperature_4" entity="Tire.Temperature_4" entType="Request">
<Component name="L1" unitsValue="" plotLabel="(Temperature)" id="520" />
<Component name="L2" unitsValue="" plotLabel="(Temperature)" id="521" />
<Component name="R1" unitsValue="" plotLabel="(Temperature)" id="522" />
<Component name="R2" unitsValue="" plotLabel="(Temperature)" id="523" />
</Entity>
<Entity name="Tire.User_Input_Contact_Patch_Global_Z_Perturbation" entity="Tire.User_Input_Contact_Patch_Global_Z_Perturbation" entType="Request">
<Component name="L1" unitsValue="meter" plotLabel="" id="524" />
<Component name="L2" unitsValue="meter" plotLabel="" id="525" />
<Component name="R1" unitsValue="meter" plotLabel="" id="526" />
<Component name="R2" unitsValue="meter" plotLabel="" id="527" />
</Entity>
<Entity name="Tire.Wear" entity="Tire.Wear" entType="Request">
<Component name="L1" unitsValue="" plotLabel="(Wear)" id="528" />
<Component name="L2" unitsValue="" plotLabel="(Wear)" id="529" />
<Component name="R1" unitsValue="" plotLabel="(Wear)" id="530" />
<Component name="R2" unitsValue="" plotLabel="(Wear)" id="531" />
</Entity>
<Entity name="Tire_front_left" entity="Tire_front_left" entType="Request">
<Component name="longitudinal_slip_actual" unitsValue="" plotLabel="(Longitudinal Slip [-1 = lockup])" id="532" />
<Component name="lateral_slip_actual" unitsValue="rad" plotLabel="()" id="533" />
<Component name="longitudinal_slip_kinematic_unbounded" unitsValue="" plotLabel="(Longitudinal Slip [-1 = lockup])" id="534" />
<Component name="lateral_slip_kinematic_unbounded" unitsValue="rad" plotLabel="()" id="535" />
<Component name="longitudinal_slip_transient_unbounded" unitsValue="" plotLabel="(Longitudinal Slip [-1 = lockup])" id="536" />
<Component name="lateral_slip_transient_unbounded" unitsValue="rad" plotLabel="()" id="537" />
<Component name="longitudinal_slip_kinematic_bounded" unitsValue="" plotLabel="(Longitudinal Slip [-1 = lockup])" id="538" />
<Component name="lateral_slip_kinematic_bounded" unitsValue="rad" plotLabel="()" id="539" />
<Component name="longitudinal_slip_transient_bounded" unitsValue="" plotLabel="(Longitudinal Slip [-1 = lockup])" id="540" />
<Component name="lateral_slip_transient_bounded" unitsValue="rad" plotLabel="()" id="541" />
</Entity>
<Entity name="Tire_front_right" entity="Tire_front_right" entType="Request">
<Component name="longitudinal_slip_actual" unitsValue="" plotLabel="(Longitudinal Slip [-1 = lockup])" id="542" />
<Component name="lateral_slip_actual" unitsValue="rad" plotLabel="()" id="543" />
<Component name="longitudinal_slip_kinematic_unbounded" unitsValue="" plotLabel="(Longitudinal Slip [-1 = lockup])" id="544" />
<Component name="lateral_slip_kinematic_unbounded" unitsValue="rad" plotLabel="()" id="545" />
<Component name="longitudinal_slip_transient_unbounded" unitsValue="" plotLabel="(Longitudinal Slip [-1 = lockup])" id="546" />
<Component name="lateral_slip_transient_unbounded" unitsValue="rad" plotLabel="()" id="547" />
<Component name="longitudinal_slip_kinematic_bounded" unitsValue="" plotLabel="(Longitudinal Slip [-1 = lockup])" id="548" />
<Component name="lateral_slip_kinematic_bounded" unitsValue="rad" plotLabel="()" id="549" />
<Component name="longitudinal_slip_transient_bounded" unitsValue="" plotLabel="(Longitudinal Slip [-1 = lockup])" id="550" />
<Component name="lateral_slip_transient_bounded" unitsValue="rad" plotLabel="()" id="551" />
</Entity>
<Entity name="Tire_rear_left" entity="Tire_rear_left" entType="Request">
<Component name="longitudinal_slip_actual" unitsValue="" plotLabel="(Longitudinal Slip [-1 = lockup])" id="552" />
<Component name="lateral_slip_actual" unitsValue="rad" plotLabel="()" id="553" />
<Component name="longitudinal_slip_kinematic_unbounded" unitsValue="" plotLabel="(Longitudinal Slip [-1 = lockup])" id="554" />
<Component name="lateral_slip_kinematic_unbounded" unitsValue="rad" plotLabel="()" id="555" />
<Component name="longitudinal_slip_transient_unbounded" unitsValue="" plotLabel="(Longitudinal Slip [-1 = lockup])" id="556" />
<Component name="lateral_slip_transient_unbounded" unitsValue="rad" plotLabel="()" id="557" />
<Component name="longitudinal_slip_kinematic_bounded" unitsValue="" plotLabel="(Longitudinal Slip [-1 = lockup])" id="558" />
<Component name="lateral_slip_kinematic_bounded" unitsValue="rad" plotLabel="()" id="559" />
<Component name="longitudinal_slip_transient_bounded" unitsValue="" plotLabel="(Longitudinal Slip [-1 = lockup])" id="560" />
<Component name="lateral_slip_transient_bounded" unitsValue="rad" plotLabel="()" id="561" />
</Entity>
<Entity name="Tire_rear_right" entity="Tire_rear_right" entType="Request">
<Component name="longitudinal_slip_actual" unitsValue="" plotLabel="(Longitudinal Slip [-1 = lockup])" id="562" />
<Component name="lateral_slip_actual" unitsValue="rad" plotLabel="()" id="563" />
<Component name="longitudinal_slip_kinematic_unbounded" unitsValue="" plotLabel="(Longitudinal Slip [-1 = lockup])" id="564" />
<Component name="lateral_slip_kinematic_unbounded" unitsValue="rad" plotLabel="()" id="565" />
<Component name="longitudinal_slip_transient_unbounded" unitsValue="" plotLabel="(Longitudinal Slip [-1 = lockup])" id="566" />
<Component name="lateral_slip_transient_unbounded" unitsValue="rad" plotLabel="()" id="567" />
<Component name="longitudinal_slip_kinematic_bounded" unitsValue="" plotLabel="(Longitudinal Slip [-1 = lockup])" id="568" />
<Component name="lateral_slip_kinematic_bounded" unitsValue="rad" plotLabel="()" id="569" />
<Component name="longitudinal_slip_transient_bounded" unitsValue="" plotLabel="(Longitudinal Slip [-1 = lockup])" id="570" />
<Component name="lateral_slip_transient_bounded" unitsValue="rad" plotLabel="()" id="571" />
</Entity>
<Entity name="Vehicle" entity="Vehicle" entType="Request">
<Component name="Body_Fixed_Alpha_X" unitsValue="radian/second**2" plotLabel="" id="572" />
<Component name="Body_Fixed_Alpha_Y" unitsValue="radian/second**2" plotLabel="" id="573" />
<Component name="Body_Fixed_Alpha_Z" unitsValue="radian/second**2" plotLabel="" id="574" />
<Component name="Body_Fixed_Omega_X" unitsValue="radian/second" plotLabel="" id="575" />
<Component name="Body_Fixed_Omega_Y" unitsValue="radian/second" plotLabel="" id="576" />
<Component name="Body_Fixed_Omega_Z" unitsValue="radian/second" plotLabel="" id="577" />
<Component name="CM_Body_Fixed_Ax" unitsValue="" plotLabel="Acceleration (g)" id="578" />
<Component name="CM_Body_Fixed_Ay" unitsValue="" plotLabel="Acceleration (g)" id="579" />
<Component name="CM_Body_Fixed_Az" unitsValue="" plotLabel="Acceleration (g)" id="580" />
<Component name="CM_Body_Fixed_Vx" unitsValue="" plotLabel="Velocity (km/h)" id="581" />
<Component name="CM_Body_Fixed_Vy" unitsValue="" plotLabel="Velocity (km/h)" id="582" />
<Component name="CM_Body_Fixed_Vz" unitsValue="" plotLabel="Velocity (km/h)" id="583" />
<Component name="CM_Global_And_Tracking_Az" unitsValue="" plotLabel="Acceleration (g)" id="584" />
<Component name="CM_Global_And_Tracking_Vz" unitsValue="" plotLabel="Velocity (km/h)" id="585" />
<Component name="CM_Global_Ax" unitsValue="" plotLabel="Acceleration (g)" id="586" />
<Component name="CM_Global_Ay" unitsValue="" plotLabel="Acceleration (g)" id="587" />
<Component name="CM_Global_Vx" unitsValue="" plotLabel="Velocity (km/h)" id="588" />
<Component name="CM_Global_Vy" unitsValue="" plotLabel="Velocity (km/h)" id="589" />
<Component name="CM_Global_X" unitsValue="meter" plotLabel="" id="590" />
<Component name="CM_Global_Y" unitsValue="meter" plotLabel="" id="591" />
<Component name="CM_Global_Z" unitsValue="meter" plotLabel="" id="592" />
<Component name="CM_Tracking_Ax" unitsValue="" plotLabel="Acceleration (g)" id="593" />
<Component name="CM_Tracking_Ay" unitsValue="" plotLabel="Acceleration (g)" id="594" />
<Component name="CM_Tracking_Vx" unitsValue="" plotLabel="Velocity (km/h)" id="595" />
<Component name="CM_Tracking_Vy" unitsValue="" plotLabel="Velocity (km/h)" id="596" />
<Component name="cross_weight_PID" unitsValue="" plotLabel="cw measure" id="597" />
<Component name="Euler_Roll" unitsValue="radian" plotLabel="" id="598" />
<Component name="front_ride_height_at_center_point" unitsValue="meter" plotLabel="" id="599" />
<Component name="Global_Alpha_X" unitsValue="radian/second**2" plotLabel="" id="600" />
<Component name="Global_Alpha_Y" unitsValue="radian/second**2" plotLabel="" id="601" />
<Component name="Global_Alpha_Z" unitsValue="radian/second**2" plotLabel="" id="602" />
<Component name="Global_Omega_X" unitsValue="radian/second" plotLabel="" id="603" />
<Component name="Global_Omega_Y" unitsValue="radian/second" plotLabel="" id="604" />
<Component name="Global_Omega_Z" unitsValue="radian/second" plotLabel="" id="605" />
<Component name="Inclination_Roll" unitsValue="radian" plotLabel="" id="606" />
<Component name="Origin_Distance_Traveled" unitsValue="meter" plotLabel="" id="607" />
<Component name="Origin_Global_X" unitsValue="meter" plotLabel="" id="608" />
<Component name="Origin_Global_Y" unitsValue="meter" plotLabel="" id="609" />
<Component name="Origin_Global_Z" unitsValue="meter" plotLabel="" id="610" />
<Component name="Origin_Global_Z_wrt_road_mk" unitsValue="meter" plotLabel="" id="611" />
<Component name="Pitch" unitsValue="radian" plotLabel="" id="612" />
<Component name="Side_Slip_Angle" unitsValue="radian" plotLabel="" id="613" />
<Component name="Side_Slip_Angle_Rate" unitsValue="radian/second" plotLabel="" id="614" />
<Component name="Understeer_Gradient" unitsValue="" plotLabel="Understeer_Gradient (deg/g)" id="615" />
<Component name="Understeer_Stability_Factor" unitsValue="" plotLabel="Understeer_Stability_Factor (rad-s**2/m**2)" id="616" />
<Component name="Yaw" unitsValue="radian" plotLabel="" id="617" />
</Entity>
<Entity name="Vehicle_States" entity="Vehicle_States" entType="Request">
<Component name="horizontal_vel_wrt_road" unitsValue="meter/second" plotLabel="" id="618" />
<Component name="lateral_acc_wrt_road" unitsValue="meter/second**2" plotLabel="" id="619" />
<Component name="lateral_disp" unitsValue="meter" plotLabel="" id="620" />
<Component name="lateral_vel_wrt_road" unitsValue="meter/second" plotLabel="" id="621" />
<Component name="longitudinal_acc_wrt_road" unitsValue="meter/second**2" plotLabel="" id="622" />
<Component name="longitudinal_disp" unitsValue="meter" plotLabel="" id="623" />
<Component name="longitudinal_vel_wrt_road" unitsValue="meter/second" plotLabel="" id="624" />
<Component name="pitch_angle" unitsValue="radian" plotLabel="" id="625" />
<Component name="pitch_angular_acc_wrt_road" unitsValue="radian/second**2" plotLabel="" id="626" />
<Component name="pitch_angular_vel_wrt_road" unitsValue="radian/second" plotLabel="" id="627" />
<Component name="roll_angle" unitsValue="radian" plotLabel="" id="628" />
<Component name="roll_angular_acc_wrt_road" unitsValue="radian/second**2" plotLabel="" id="629" />
<Component name="roll_angular_vel_wrt_road" unitsValue="radian/second" plotLabel="" id="630" />
<Component name="side_slip" unitsValue="radian" plotLabel="" id="631" />
<Component name="vertical_acc_wrt_road" unitsValue="meter/second**2" plotLabel="" id="632" />
<Component name="vertical_disp" unitsValue="meter" plotLabel="" id="633" />
<Component name="vertical_vel_wrt_road" unitsValue="meter/second" plotLabel="" id="634" />
<Component name="yaw_angle" unitsValue="radian" plotLabel="" id="635" />
<Component name="yaw_angular_acc_wrt_road" unitsValue="radian/second**2" plotLabel="" id="636" />
<Component name="yaw_angular_vel_wrt_road" unitsValue="radian/second" plotLabel="" id="637" />
</Entity>
<Entity name="Wheel.Alpha" entity="Wheel.Alpha" entType="Request">
<Component name="L1" unitsValue="radian/second**2" plotLabel="" id="638" />
<Component name="L2" unitsValue="radian/second**2" plotLabel="" id="639" />
<Component name="R1" unitsValue="radian/second**2" plotLabel="" id="640" />
<Component name="R2" unitsValue="radian/second**2" plotLabel="" id="641" />
</Entity>
<Entity name="Wheel.Caster_Angle" entity="Wheel.Caster_Angle" entType="Request">
<Component name="left" unitsValue="radian" plotLabel="" id="642" />
<Component name="right" unitsValue="radian" plotLabel="" id="643" />
</Entity>
<Entity name="Wheel.Drive_Moment" entity="Wheel.Drive_Moment" entType="Request">
<Component name="L1" unitsValue="newton-meter" plotLabel="" id="644" />
<Component name="L2" unitsValue="newton-meter" plotLabel="" id="645" />
<Component name="R1" unitsValue="newton-meter" plotLabel="" id="646" />
<Component name="R2" unitsValue="newton-meter" plotLabel="" id="647" />
</Entity>
<Entity name="Wheel.Euler_Roll" entity="Wheel.Euler_Roll" entType="Request">
<Component name="L1" unitsValue="radian" plotLabel="" id="648" />
<Component name="L2" unitsValue="radian" plotLabel="" id="649" />
<Component name="R1" unitsValue="radian" plotLabel="" id="650" />
<Component name="R2" unitsValue="radian" plotLabel="" id="651" />
</Entity>
<Entity name="Wheel.Global_Omega_X" entity="Wheel.Global_Omega_X" entType="Request">
<Component name="L1" unitsValue="radian/second" plotLabel="" id="652" />
<Component name="L2" unitsValue="radian/second" plotLabel="" id="653" />
<Component name="R1" unitsValue="radian/second" plotLabel="" id="654" />
<Component name="R2" unitsValue="radian/second" plotLabel="" id="655" />
</Entity>
<Entity name="Wheel.Global_Omega_Y" entity="Wheel.Global_Omega_Y" entType="Request">
<Component name="L1" unitsValue="radian/second" plotLabel="" id="656" />
<Component name="L2" unitsValue="radian/second" plotLabel="" id="657" />
<Component name="R1" unitsValue="radian/second" plotLabel="" id="658" />
<Component name="R2" unitsValue="radian/second" plotLabel="" id="659" />
</Entity>
<Entity name="Wheel.Global_Omega_Z" entity="Wheel.Global_Omega_Z" entType="Request">
<Component name="L1" unitsValue="radian/second" plotLabel="" id="660" />
<Component name="L2" unitsValue="radian/second" plotLabel="" id="661" />
<Component name="R1" unitsValue="radian/second" plotLabel="" id="662" />
<Component name="R2" unitsValue="radian/second" plotLabel="" id="663" />
</Entity>
<Entity name="Wheel.Global_Vx" entity="Wheel.Global_Vx" entType="Request">
<Component name="L1" unitsValue="" plotLabel="Velocity (km/h)" id="664" />
<Component name="L2" unitsValue="" plotLabel="Velocity (km/h)" id="665" />
<Component name="R1" unitsValue="" plotLabel="Velocity (km/h)" id="666" />
<Component name="R2" unitsValue="" plotLabel="Velocity (km/h)" id="667" />
</Entity>
<Entity name="Wheel.Global_Vy" entity="Wheel.Global_Vy" entType="Request">
<Component name="L1" unitsValue="" plotLabel="Velocity (km/h)" id="668" />
<Component name="L2" unitsValue="" plotLabel="Velocity (km/h)" id="669" />
<Component name="R1" unitsValue="" plotLabel="Velocity (km/h)" id="670" />
<Component name="R2" unitsValue="" plotLabel="Velocity (km/h)" id="671" />
</Entity>
<Entity name="Wheel.Global_Vz" entity="Wheel.Global_Vz" entType="Request">
<Component name="L1" unitsValue="" plotLabel="Velocity (km/h)" id="672" />
<Component name="L2" unitsValue="" plotLabel="Velocity (km/h)" id="673" />
<Component name="R1" unitsValue="" plotLabel="Velocity (km/h)" id="674" />
<Component name="R2" unitsValue="" plotLabel="Velocity (km/h)" id="675" />
</Entity>
<Entity name="Wheel.Global_X" entity="Wheel.Global_X" entType="Request">
<Component name="L1" unitsValue="meter" plotLabel="" id="676" />
<Component name="L2" unitsValue="meter" plotLabel="" id="677" />
<Component name="R1" unitsValue="meter" plotLabel="" id="678" />
<Component name="R2" unitsValue="meter" plotLabel="" id="679" />
</Entity>
<Entity name="Wheel.Global_Y" entity="Wheel.Global_Y" entType="Request">
<Component name="L1" unitsValue="meter" plotLabel="" id="680" />
<Component name="L2" unitsValue="meter" plotLabel="" id="681" />
<Component name="R1" unitsValue="meter" plotLabel="" id="682" />
<Component name="R2" unitsValue="meter" plotLabel="" id="683" />
</Entity>
<Entity name="Wheel.Global_Z" entity="Wheel.Global_Z" entType="Request">
<Component name="L1" unitsValue="meter" plotLabel="" id="684" />
<Component name="L2" unitsValue="meter" plotLabel="" id="685" />
<Component name="R1" unitsValue="meter" plotLabel="" id="686" />
<Component name="R2" unitsValue="meter" plotLabel="" id="687" />
</Entity>
<Entity name="Wheel.Ground_Surface_Wheel_Center_Vx" entity="Wheel.Ground_Surface_Wheel_Center_Vx" entType="Request">
<Component name="L1" unitsValue="" plotLabel="Velocity (km/h)" id="688" />
<Component name="L2" unitsValue="" plotLabel="Velocity (km/h)" id="689" />
<Component name="R1" unitsValue="" plotLabel="Velocity (km/h)" id="690" />
<Component name="R2" unitsValue="" plotLabel="Velocity (km/h)" id="691" />
</Entity>
<Entity name="Wheel.Hub_Carrier_Omega_X" entity="Wheel.Hub_Carrier_Omega_X" entType="Request">
<Component name="L1" unitsValue="radian/second" plotLabel="" id="692" />
<Component name="L2" unitsValue="radian/second" plotLabel="" id="693" />
<Component name="R1" unitsValue="radian/second" plotLabel="" id="694" />
<Component name="R2" unitsValue="radian/second" plotLabel="" id="695" />
</Entity>
<Entity name="Wheel.Hub_Carrier_Omega_Y" entity="Wheel.Hub_Carrier_Omega_Y" entType="Request">
<Component name="L1" unitsValue="radian/second" plotLabel="" id="696" />
<Component name="L2" unitsValue="radian/second" plotLabel="" id="697" />
<Component name="R1" unitsValue="radian/second" plotLabel="" id="698" />
<Component name="R2" unitsValue="radian/second" plotLabel="" id="699" />
</Entity>
<Entity name="Wheel.Hub_Carrier_Omega_Z" entity="Wheel.Hub_Carrier_Omega_Z" entType="Request">
<Component name="L1" unitsValue="radian/second" plotLabel="" id="700" />
<Component name="L2" unitsValue="radian/second" plotLabel="" id="701" />
<Component name="R1" unitsValue="radian/second" plotLabel="" id="702" />
<Component name="R2" unitsValue="radian/second" plotLabel="" id="703" />
</Entity>
<Entity name="Wheel.Hub_Carrier_Vx" entity="Wheel.Hub_Carrier_Vx" entType="Request">
<Component name="L1" unitsValue="" plotLabel="Velocity (km/h)" id="704" />
<Component name="L2" unitsValue="" plotLabel="Velocity (km/h)" id="705" />
<Component name="R1" unitsValue="" plotLabel="Velocity (km/h)" id="706" />
<Component name="R2" unitsValue="" plotLabel="Velocity (km/h)" id="707" />
</Entity>
<Entity name="Wheel.Hub_Carrier_Vy" entity="Wheel.Hub_Carrier_Vy" entType="Request">
<Component name="L1" unitsValue="" plotLabel="Velocity (km/h)" id="708" />
<Component name="L2" unitsValue="" plotLabel="Velocity (km/h)" id="709" />
<Component name="R1" unitsValue="" plotLabel="Velocity (km/h)" id="710" />
<Component name="R2" unitsValue="" plotLabel="Velocity (km/h)" id="711" />
</Entity>
<Entity name="Wheel.Hub_Carrier_Vz" entity="Wheel.Hub_Carrier_Vz" entType="Request">
<Component name="L1" unitsValue="" plotLabel="Velocity (km/h)" id="712" />
<Component name="L2" unitsValue="" plotLabel="Velocity (km/h)" id="713" />
<Component name="R1" unitsValue="" plotLabel="Velocity (km/h)" id="714" />
<Component name="R2" unitsValue="" plotLabel="Velocity (km/h)" id="715" />
</Entity>
<Entity name="Wheel.Inclination" entity="Wheel.Inclination" entType="Request">
<Component name="L1" unitsValue="radian" plotLabel="" id="716" />
<Component name="L2" unitsValue="radian" plotLabel="" id="717" />
<Component name="R1" unitsValue="radian" plotLabel="" id="718" />
<Component name="R2" unitsValue="radian" plotLabel="" id="719" />
</Entity>
<Entity name="Wheel.Kingpin_Moment" entity="Wheel.Kingpin_Moment" entType="Request">
<Component name="L1" unitsValue="newton-meter" plotLabel="" id="720" />
<Component name="R1" unitsValue="newton-meter" plotLabel="" id="721" />
</Entity>
<Entity name="Wheel.Omega" entity="Wheel.Omega" entType="Request">
<Component name="L1" unitsValue="radian/second" plotLabel="" id="722" />
<Component name="L2" unitsValue="radian/second" plotLabel="" id="723" />
<Component name="R1" unitsValue="radian/second" plotLabel="" id="724" />
<Component name="R2" unitsValue="radian/second" plotLabel="" id="725" />
</Entity>
<Entity name="Wheel.Phi" entity="Wheel.Phi" entType="Request">
<Component name="L1" unitsValue="radian" plotLabel="" id="726" />
<Component name="L2" unitsValue="radian" plotLabel="" id="727" />
<Component name="R1" unitsValue="radian" plotLabel="" id="728" />
<Component name="R2" unitsValue="radian" plotLabel="" id="729" />
</Entity>
<Entity name="Wheel.Pitch" entity="Wheel.Pitch" entType="Request">
<Component name="L1" unitsValue="radian" plotLabel="" id="730" />
<Component name="L2" unitsValue="radian" plotLabel="" id="731" />
<Component name="R1" unitsValue="radian" plotLabel="" id="732" />
<Component name="R2" unitsValue="radian" plotLabel="" id="733" />
</Entity>
<Entity name="Wheel.Psi" entity="Wheel.Psi" entType="Request">
<Component name="L1" unitsValue="radian" plotLabel="" id="734" />
<Component name="L2" unitsValue="radian" plotLabel="" id="735" />
<Component name="R1" unitsValue="radian" plotLabel="" id="736" />
<Component name="R2" unitsValue="radian" plotLabel="" id="737" />
</Entity>
<Entity name="Wheel.Rotation" entity="Wheel.Rotation" entType="Request">
<Component name="L1" unitsValue="radian" plotLabel="" id="738" />
<Component name="L2" unitsValue="radian" plotLabel="" id="739" />
<Component name="R1" unitsValue="radian" plotLabel="" id="740" />
<Component name="R2" unitsValue="radian" plotLabel="" id="741" />
</Entity>
<Entity name="Wheel.Side_View_Angle" entity="Wheel.Side_View_Angle" entType="Request">
<Component name="L1" unitsValue="radian" plotLabel="" id="742" />
<Component name="L2" unitsValue="radian" plotLabel="" id="743" />
<Component name="R1" unitsValue="radian" plotLabel="" id="744" />
<Component name="R2" unitsValue="radian" plotLabel="" id="745" />
</Entity>
<Entity name="Wheel.Spindle_Steer" entity="Wheel.Spindle_Steer" entType="Request">
<Component name="L1" unitsValue="radian" plotLabel="" id="746" />
<Component name="L2" unitsValue="radian" plotLabel="" id="747" />
<Component name="R1" unitsValue="radian" plotLabel="" id="748" />
<Component name="R2" unitsValue="radian" plotLabel="" id="749" />
</Entity>
<Entity name="Wheel.Theta" entity="Wheel.Theta" entType="Request">
<Component name="L1" unitsValue="radian" plotLabel="" id="750" />
<Component name="L2" unitsValue="radian" plotLabel="" id="751" />
<Component name="R1" unitsValue="radian" plotLabel="" id="752" />
<Component name="R2" unitsValue="radian" plotLabel="" id="753" />
</Entity>
<Entity name="Wheel.Yaw" entity="Wheel.Yaw" entType="Request">
<Component name="L1" unitsValue="radian" plotLabel="" id="754" />
<Component name="L2" unitsValue="radian" plotLabel="" id="755" />
<Component name="R1" unitsValue="radian" plotLabel="" id="756" />
<Component name="R2" unitsValue="radian" plotLabel="" id="757" />
</Entity>
<Entity name="Wheel.hub_center_accx" entity="Wheel.hub_center_accx" entType="Request">
<Component name="front_left" unitsValue="meter/second**2" plotLabel="" id="758" />
<Component name="front_right" unitsValue="meter/second**2" plotLabel="" id="759" />
<Component name="rear_left" unitsValue="meter/second**2" plotLabel="" id="760" />
<Component name="rear_right" unitsValue="meter/second**2" plotLabel="" id="761" />
</Entity>
<Entity name="Wheel.hub_center_accy" entity="Wheel.hub_center_accy" entType="Request">
<Component name="front_left" unitsValue="meter/second**2" plotLabel="" id="762" />
<Component name="front_right" unitsValue="meter/second**2" plotLabel="" id="763" />
<Component name="rear_left" unitsValue="meter/second**2" plotLabel="" id="764" />
<Component name="rear_right" unitsValue="meter/second**2" plotLabel="" id="765" />
</Entity>
<Entity name="Wheel.hub_center_accz" entity="Wheel.hub_center_accz" entType="Request">
<Component name="front_left" unitsValue="meter/second**2" plotLabel="" id="766" />
<Component name="front_right" unitsValue="meter/second**2" plotLabel="" id="767" />
<Component name="rear_left" unitsValue="meter/second**2" plotLabel="" id="768" />
<Component name="rear_right" unitsValue="meter/second**2" plotLabel="" id="769" />
</Entity>
<Entity name="Wheel.wheel_center_dispx" entity="Wheel.wheel_center_dispx" entType="Request">
<Component name="front_left" unitsValue="meter" plotLabel="" id="770" />
<Component name="front_right" unitsValue="meter" plotLabel="" id="771" />
<Component name="rear_left" unitsValue="meter" plotLabel="" id="772" />
<Component name="rear_right" unitsValue="meter" plotLabel="" id="773" />
</Entity>
<Entity name="Wheel.wheel_center_dispy" entity="Wheel.wheel_center_dispy" entType="Request">
<Component name="front_left" unitsValue="meter" plotLabel="" id="774" />
<Component name="front_right" unitsValue="meter" plotLabel="" id="775" />
<Component name="rear_left" unitsValue="meter" plotLabel="" id="776" />
<Component name="rear_right" unitsValue="meter" plotLabel="" id="777" />
</Entity>
<Entity name="Wheel.wheel_center_dispz" entity="Wheel.wheel_center_dispz" entType="Request">
<Component name="front_left" unitsValue="meter" plotLabel="" id="778" />
<Component name="front_right" unitsValue="meter" plotLabel="" id="779" />
<Component name="rear_left" unitsValue="meter" plotLabel="" id="780" />
<Component name="rear_right" unitsValue="meter" plotLabel="" id="781" />
</Entity>
<Entity name="accel grav_sensor" entity="accel grav_sensor" entType="Request">
<Component name="ACCX_with_gravity" unitsValue="meter/second**2" plotLabel="" id="782" />
<Component name="ACCY_with_gravity" unitsValue="meter/second**2" plotLabel="" id="783" />
<Component name="ACCZ_with_gravity" unitsValue="meter/second**2" plotLabel="" id="784" />
</Entity>
<Entity name="aero_forces" entity="aero_forces" entType="Request">
<Component name="aero_balance" unitsValue="" plotLabel="" id="785" />
<Component name="center_downforce" unitsValue="newton" plotLabel="" id="786" />
<Component name="center_sideforce" unitsValue="newton" plotLabel="" id="787" />
<Component name="drag_arm" unitsValue="meter" plotLabel="" id="788" />
<Component name="drag_force" unitsValue="newton" plotLabel="" id="789" />
<Component name="drag_force_front" unitsValue="newton" plotLabel="" id="790" />
<Component name="drag_force_rear" unitsValue="newton" plotLabel="" id="791" />
<Component name="drag_torque" unitsValue="newton-meter" plotLabel="" id="792" />
<Component name="front_downforce" unitsValue="newton" plotLabel="" id="793" />
<Component name="front_sideforce" unitsValue="newton" plotLabel="" id="794" />
<Component name="height_auxiliary" unitsValue="meter" plotLabel="" id="795" />
<Component name="height_front" unitsValue="meter" plotLabel="" id="796" />
<Component name="height_rear" unitsValue="meter" plotLabel="" id="797" />
<Component name="lateral_velocity" unitsValue="meter/second" plotLabel="" id="798" />
<Component name="longitudinal_velocity" unitsValue="meter/second" plotLabel="" id="799" />
<Component name="pitch" unitsValue="radian" plotLabel="" id="800" />
<Component name="rear_downforce" unitsValue="newton" plotLabel="" id="801" />
<Component name="rear_sideforce" unitsValue="newton" plotLabel="" id="802" />
<Component name="roll" unitsValue="radian" plotLabel="" id="803" />
<Component name="roll_torque" unitsValue="newton-meter" plotLabel="" id="804" />
<Component name="side_slip" unitsValue="radian" plotLabel="" id="805" />
<Component name="steer" unitsValue="radian" plotLabel="" id="806" />
<Component name="vertical_velocity" unitsValue="meter/second" plotLabel="" id="807" />
<Component name="yaw_torque" unitsValue="newton-meter" plotLabel="" id="808" />
</Entity>
<Entity name="bul_jounce_stop_data" entity="bul_jounce_stop_data" entType="Request">
<Component name="force_front" unitsValue="newton" plotLabel="" id="809" />
<Component name="force_rear" unitsValue="newton" plotLabel="" id="810" />
<Component name="jounce_front" unitsValue="meter" plotLabel="" id="811" />
<Component name="jounce_rear" unitsValue="meter" plotLabel="" id="812" />
<Component name="velocity_front" unitsValue="meter/second" plotLabel="" id="813" />
<Component name="velocity_rear" unitsValue="meter/second" plotLabel="" id="814" />
</Entity>
<Entity name="bul_rebound_stop_data" entity="bul_rebound_stop_data" entType="Request">
<Component name="force_front" unitsValue="newton" plotLabel="" id="815" />
<Component name="force_rear" unitsValue="newton" plotLabel="" id="816" />
<Component name="jounce_front" unitsValue="meter" plotLabel="" id="817" />
<Component name="jounce_rear" unitsValue="meter" plotLabel="" id="818" />
<Component name="velocity_front" unitsValue="meter/second" plotLabel="" id="819" />
<Component name="velocity_rear" unitsValue="meter/second" plotLabel="" id="820" />
</Entity>
<Entity name="bur_jounce_stop_data" entity="bur_jounce_stop_data" entType="Request">
<Component name="force_front" unitsValue="newton" plotLabel="" id="821" />
<Component name="force_rear" unitsValue="newton" plotLabel="" id="822" />
<Component name="jounce_front" unitsValue="meter" plotLabel="" id="823" />
<Component name="jounce_rear" unitsValue="meter" plotLabel="" id="824" />
<Component name="velocity_front" unitsValue="meter/second" plotLabel="" id="825" />
<Component name="velocity_rear" unitsValue="meter/second" plotLabel="" id="826" />
</Entity>
<Entity name="bur_rebound_stop_data" entity="bur_rebound_stop_data" entType="Request">
<Component name="force_front" unitsValue="newton" plotLabel="" id="827" />
<Component name="force_rear" unitsValue="newton" plotLabel="" id="828" />
<Component name="jounce_front" unitsValue="meter" plotLabel="" id="829" />
<Component name="jounce_rear" unitsValue="meter" plotLabel="" id="830" />
<Component name="velocity_front" unitsValue="meter/second" plotLabel="" id="831" />
<Component name="velocity_rear" unitsValue="meter/second" plotLabel="" id="832" />
</Entity>
<Entity name="chassis_accelerations" entity="chassis_accelerations" entType="Request">
<Component name="lateral" unitsValue="" plotLabel="Acceleration (g)" id="833" />
<Component name="longitudinal" unitsValue="" plotLabel="Acceleration (g)" id="834" />
<Component name="pitch" unitsValue="radian/second**2" plotLabel="" id="835" />
<Component name="roll" unitsValue="radian/second**2" plotLabel="" id="836" />
<Component name="vertical" unitsValue="" plotLabel="Acceleration (g)" id="837" />
<Component name="yaw" unitsValue="radian/second**2" plotLabel="" id="838" />
</Entity>
<Entity name="chassis_displacements" entity="chassis_displacements" entType="Request">
<Component name="lateral" unitsValue="meter" plotLabel="" id="839" />
<Component name="longitudinal" unitsValue="meter" plotLabel="" id="840" />
<Component name="pitch" unitsValue="radian" plotLabel="" id="841" />
<Component name="pitch_wrt_road" unitsValue="radian" plotLabel="" id="842" />
<Component name="roll" unitsValue="radian" plotLabel="" id="843" />
<Component name="roll_wrt_road" unitsValue="radian" plotLabel="" id="844" />
<Component name="vertical" unitsValue="meter" plotLabel="" id="845" />
<Component name="vertical_wrt_road" unitsValue="meter" plotLabel="" id="846" />
<Component name="yaw" unitsValue="radian" plotLabel="" id="847" />
</Entity>
<Entity name="chassis_velocities" entity="chassis_velocities" entType="Request">
<Component name="lateral" unitsValue="" plotLabel="Velocity (km/h)" id="848" />
<Component name="longitudinal" unitsValue="" plotLabel="Velocity (km/h)" id="849" />
<Component name="pitch" unitsValue="radian/second" plotLabel="" id="850" />
<Component name="roll" unitsValue="radian/second" plotLabel="" id="851" />
<Component name="vertical" unitsValue="" plotLabel="Velocity (km/h)" id="852" />
<Component name="yaw" unitsValue="radian/second" plotLabel="" id="853" />
</Entity>
<Entity name="clutch" entity="clutch" entType="Request">
<Component name="clutch_rpm" unitsValue="" plotLabel="(RPM)" id="854" />
<Component name="effective_clutch" unitsValue="" plotLabel="clutch demand [0 to 1] (-)" id="855" />
<Component name="gearbox_inputshaft_alpha" unitsValue="radian/second**2" plotLabel="" id="856" />
<Component name="gearbox_inputshaft_angle" unitsValue="radian" plotLabel="" id="857" />
<Component name="gearbox_inputshaft_omega" unitsValue="radian/second" plotLabel="" id="858" />
<Component name="inputplate_torque" unitsValue="newton-meter" plotLabel="" id="859" />
<Component name="slip_angle" unitsValue="radian" plotLabel="" id="860" />
<Component name="torque" unitsValue="newton-meter" plotLabel="" id="861" />
</Entity>
<Entity name="condition_sensors" entity="condition_sensors" entType="Request">
<Component name="side_slip_angle" unitsValue="radian" plotLabel="" id="862" />
</Entity>
<Entity name="cp_force_lateralFL" entity="cp_force_lateralFL" entType="Part">
<Component name="X" unitsValue="newton" plotLabel="" id="863" />
<Component name="Y" unitsValue="newton" plotLabel="" id="864" />
<Component name="Z" unitsValue="newton" plotLabel="" id="865" />
</Entity>
<Entity name="cp_force_lateralFR" entity="cp_force_lateralFR" entType="Part">
<Component name="X" unitsValue="newton" plotLabel="" id="866" />
<Component name="Y" unitsValue="newton" plotLabel="" id="867" />
<Component name="Z" unitsValue="newton" plotLabel="" id="868" />
</Entity>
<Entity name="cp_force_lateralRL" entity="cp_force_lateralRL" entType="Part">
<Component name="X" unitsValue="newton" plotLabel="" id="869" />
<Component name="Y" unitsValue="newton" plotLabel="" id="870" />
<Component name="Z" unitsValue="newton" plotLabel="" id="871" />
</Entity>
<Entity name="cp_force_lateralRR" entity="cp_force_lateralRR" entType="Part">
<Component name="X" unitsValue="newton" plotLabel="" id="872" />
<Component name="Y" unitsValue="newton" plotLabel="" id="873" />
<Component name="Z" unitsValue="newton" plotLabel="" id="874" />
</Entity>
<Entity name="cp_force_longitudinalFL" entity="cp_force_longitudinalFL" entType="Part">
<Component name="X" unitsValue="newton" plotLabel="" id="875" />
<Component name="Y" unitsValue="newton" plotLabel="" id="876" />
<Component name="Z" unitsValue="newton" plotLabel="" id="877" />
</Entity>
<Entity name="cp_force_longitudinalFR" entity="cp_force_longitudinalFR" entType="Part">
<Component name="X" unitsValue="newton" plotLabel="" id="878" />
<Component name="Y" unitsValue="newton" plotLabel="" id="879" />
<Component name="Z" unitsValue="newton" plotLabel="" id="880" />
</Entity>
<Entity name="cp_force_longitudinalRL" entity="cp_force_longitudinalRL" entType="Part">
<Component name="X" unitsValue="newton" plotLabel="" id="881" />
<Component name="Y" unitsValue="newton" plotLabel="" id="882" />
<Component name="Z" unitsValue="newton" plotLabel="" id="883" />
</Entity>
<Entity name="cp_force_longitudinalRR" entity="cp_force_longitudinalRR" entType="Part">
<Component name="X" unitsValue="newton" plotLabel="" id="884" />
<Component name="Y" unitsValue="newton" plotLabel="" id="885" />
<Component name="Z" unitsValue="newton" plotLabel="" id="886" />
</Entity>
<Entity name="cp_force_normalFL" entity="cp_force_normalFL" entType="Part">
<Component name="X" unitsValue="newton" plotLabel="" id="887" />
<Component name="Y" unitsValue="newton" plotLabel="" id="888" />
<Component name="Z" unitsValue="newton" plotLabel="" id="889" />
</Entity>
<Entity name="cp_force_normalFR" entity="cp_force_normalFR" entType="Part">
<Component name="X" unitsValue="newton" plotLabel="" id="890" />
<Component name="Y" unitsValue="newton" plotLabel="" id="891" />
<Component name="Z" unitsValue="newton" plotLabel="" id="892" />
</Entity>
<Entity name="cp_force_normalRL" entity="cp_force_normalRL" entType="Part">
<Component name="X" unitsValue="newton" plotLabel="" id="893" />
<Component name="Y" unitsValue="newton" plotLabel="" id="894" />
<Component name="Z" unitsValue="newton" plotLabel="" id="895" />
</Entity>
<Entity name="cp_force_normalRR" entity="cp_force_normalRR" entType="Part">
<Component name="X" unitsValue="newton" plotLabel="" id="896" />
<Component name="Y" unitsValue="newton" plotLabel="" id="897" />
<Component name="Z" unitsValue="newton" plotLabel="" id="898" />
</Entity>
<Entity name="cross_weight" entity="cross_weight" entType="Request">
<Component name="crossL1R2_ratio" unitsValue="" plotLabel="percentage" id="899" />
<Component name="crossR1L2_ratio" unitsValue="" plotLabel="percentage" id="900" />
<Component name="nose_ratio" unitsValue="" plotLabel="percentage" id="901" />
<Component name="side_right_ratio" unitsValue="" plotLabel="percentage" id="902" />
</Entity>
<Entity name="dal_ride_damper_data" entity="dal_ride_damper_data" entType="Request">
<Component name="force_front" unitsValue="newton" plotLabel="" id="903" />
<Component name="force_rear" unitsValue="newton" plotLabel="" id="904" />
<Component name="velocity_front" unitsValue="meter/second" plotLabel="" id="905" />
<Component name="velocity_rear" unitsValue="meter/second" plotLabel="" id="906" />
</Entity>
<Entity name="dar_ride_damper_data" entity="dar_ride_damper_data" entType="Request">
<Component name="force_front" unitsValue="newton" plotLabel="" id="907" />
<Component name="force_rear" unitsValue="newton" plotLabel="" id="908" />
<Component name="velocity_front" unitsValue="meter/second" plotLabel="" id="909" />
<Component name="velocity_rear" unitsValue="meter/second" plotLabel="" id="910" />
</Entity>
<Entity name="differential_central" entity="differential_central" entType="Request">
<Component name="diff_front_inputshaft_alpha" unitsValue="radian/second**2" plotLabel="" id="911" />
<Component name="diff_front_inputshaft_angle" unitsValue="radian" plotLabel="" id="912" />
<Component name="diff_front_inputshaft_omega" unitsValue="radian/second" plotLabel="" id="913" />
<Component name="diff_rear_inputshaft_alpha" unitsValue="radian/second**2" plotLabel="" id="914" />
<Component name="diff_rear_inputshaft_angle" unitsValue="radian" plotLabel="" id="915" />
<Component name="diff_rear_inputshaft_omega" unitsValue="radian/second" plotLabel="" id="916" />
<Component name="gearbox_outputshaft_torque" unitsValue="newton*meter" plotLabel="" id="917" />
</Entity>
<Entity name="differential_front" entity="differential_front" entType="Request">
<Component name="diff_central_front_outputshaft_torque" unitsValue="newton*meter" plotLabel="" id="918" />
<Component name="wheel_front_left_alpha" unitsValue="radian/second**2" plotLabel="" id="919" />
<Component name="wheel_front_left_angle" unitsValue="radian" plotLabel="" id="920" />
<Component name="wheel_front_left_omega" unitsValue="radian/second" plotLabel="" id="921" />
<Component name="wheel_front_right_alpha" unitsValue="radian/second**2" plotLabel="" id="922" />
<Component name="wheel_front_right_angle" unitsValue="radian" plotLabel="" id="923" />
<Component name="wheel_front_right_omega" unitsValue="radian/second" plotLabel="" id="924" />
</Entity>
<Entity name="differential_rear" entity="differential_rear" entType="Request">
<Component name="diff_central_rear_outputshaft_torque" unitsValue="newton*meter" plotLabel="" id="925" />
<Component name="wheel_rear_left_alpha" unitsValue="radian/second**2" plotLabel="" id="926" />
<Component name="wheel_rear_left_angle" unitsValue="radian" plotLabel="" id="927" />
<Component name="wheel_rear_left_omega" unitsValue="radian/second" plotLabel="" id="928" />
<Component name="wheel_rear_right_alpha" unitsValue="radian/second**2" plotLabel="" id="929" />
<Component name="wheel_rear_right_angle" unitsValue="radian" plotLabel="" id="930" />
<Component name="wheel_rear_right_omega" unitsValue="radian/second" plotLabel="" id="931" />
</Entity>
<Entity name="differential_speeds" entity="differential_speeds" entType="Request">
<Component name="halfshaft_omega_central_front" unitsValue="radian/sec" plotLabel="" id="932" />
<Component name="halfshaft_omega_central_rear" unitsValue="radian/sec" plotLabel="" id="933" />
<Component name="halfshaft_omega_delta_central" unitsValue="radian/sec" plotLabel="" id="934" />
<Component name="halfshaft_omega_delta_front" unitsValue="radian/sec" plotLabel="" id="935" />
<Component name="halfshaft_omega_delta_rear" unitsValue="radian/sec" plotLabel="" id="936" />
<Component name="halfshaft_omega_left_front" unitsValue="radian/sec" plotLabel="" id="937" />
<Component name="halfshaft_omega_left_rear" unitsValue="radian/sec" plotLabel="" id="938" />
<Component name="halfshaft_omega_right_front" unitsValue="radian/sec" plotLabel="" id="939" />
<Component name="halfshaft_omega_right_rear" unitsValue="radian/sec" plotLabel="" id="940" />
</Entity>
<Entity name="differential_torques" entity="differential_torques" entType="Request">
<Component name="differential_torque_central" unitsValue="newton-meter" plotLabel="" id="941" />
<Component name="differential_torque_front" unitsValue="newton-meter" plotLabel="" id="942" />
<Component name="differential_torque_rear" unitsValue="newton-meter" plotLabel="" id="943" />
<Component name="output_torque_central_front" unitsValue="newton-meter" plotLabel="" id="944" />
<Component name="output_torque_central_rear" unitsValue="newton-meter" plotLabel="" id="945" />
<Component name="output_torque_left_front" unitsValue="newton-meter" plotLabel="" id="946" />
<Component name="output_torque_left_rear" unitsValue="newton-meter" plotLabel="" id="947" />
<Component name="output_torque_right_front" unitsValue="newton-meter" plotLabel="" id="948" />
<Component name="output_torque_right_rear" unitsValue="newton-meter" plotLabel="" id="949" />
</Entity>
<Entity name="disp_sensor" entity="disp_sensor" entType="Request">
<Component name="X" unitsValue="meter" plotLabel="" id="950" />
<Component name="Y" unitsValue="meter" plotLabel="" id="951" />
<Component name="Z" unitsValue="meter" plotLabel="" id="952" />
</Entity>
<Entity name="driverEYE_sensor" entity="driverEYE_sensor" entType="Request">
<Component name="ACCX" unitsValue="meter/second**2" plotLabel="" id="953" />
<Component name="ACCY" unitsValue="meter/second**2" plotLabel="" id="954" />
<Component name="ACCZ" unitsValue="meter/second**2" plotLabel="" id="955" />
</Entity>
<Entity name="driver_demands" entity="driver_demands" entType="Request">
<Component name="brake" unitsValue="" plotLabel="Brake Signal [0 to 100]" id="956" />
<Component name="brake_pressure" unitsValue="" plotLabel="Pressure (MPa)" id="957" />
<Component name="clutch" unitsValue="" plotLabel="Clutch [0 to 1]" id="958" />
<Component name="gear" unitsValue="" plotLabel="Gear" id="959" />
<Component name="steering" unitsValue="radian" plotLabel="" id="960" />
<Component name="steering_velocity" unitsValue="radian/second" plotLabel="" id="961" />
<Component name="throttle" unitsValue="" plotLabel="Engine Throttle [0 to 100]" id="962" />
</Entity>
<Entity name="driving_machine_monitor" entity="driving_machine_monitor" entType="Request">
<Component name="driver_brake" unitsValue="" plotLabel="Brake Signal [0 to 100]" id="963" />
<Component name="driver_clutch" unitsValue="" plotLabel="Clutch [0 to 1]" id="964" />
<Component name="driver_gear" unitsValue="" plotLabel="Gear" id="965" />
<Component name="driver_steering" unitsValue="radian" plotLabel="" id="966" />
<Component name="driver_throttle" unitsValue="" plotLabel="Engine Throttle [0 to 100]" id="967" />
<Component name="maneuver_ID" unitsValue="" plotLabel="Mini_Maneuver_ID" id="968" />
<Component name="path_curvature" unitsValue="" plotLabel="Curvature (1/m)" id="969" />
<Component name="path_distance" unitsValue="meter" plotLabel="" id="970" />
<Component name="path_s" unitsValue="meter" plotLabel="" id="971" />
<Component name="path_x" unitsValue="meter" plotLabel="" id="972" />
<Component name="path_y" unitsValue="meter" plotLabel="" id="973" />
<Component name="path_z" unitsValue="meter" plotLabel="" id="974" />
<Component name="target_ax" unitsValue="" plotLabel="Acceleration (g)" id="975" />
<Component name="target_engine_torque" unitsValue="newton-meter" plotLabel="" id="976" />
<Component name="target_vx" unitsValue="" plotLabel="Velocity (km/h)" id="977" />
</Entity>
<Entity name="engine" entity="engine" entType="Request">
<Component name="clutch_inputplate_alpha" unitsValue="radian/second**2" plotLabel="" id="978" />
<Component name="clutch_inputplate_angle" unitsValue="radian" plotLabel="" id="979" />
<Component name="clutch_inputplate_omega" unitsValue="radian/second" plotLabel="" id="980" />
<Component name="effective_throttle" unitsValue="" plotLabel="Engine Throttle [0 to 100] (-)" id="981" />
<Component name="engine_rpm" unitsValue="" plotLabel="(RPM)" id="982" />
<Component name="Max_Engine_torque" unitsValue="newton-meter" plotLabel="" id="983" />
<Component name="Min_engine_torque" unitsValue="newton-meter" plotLabel="" id="984" />
<Component name="Power_HP" unitsValue="" plotLabel="(Hp)" id="985" />
<Component name="Power_KW" unitsValue="" plotLabel="(KW)" id="986" />
<Component name="TCS_activity" unitsValue="" plotLabel="Traction_Control_Activation (-)" id="987" />
<Component name="torque" unitsValue="newton-meter" plotLabel="" id="988" />
</Entity>
<Entity name="fuel_consumption" entity="fuel_consumption" entType="Request">
<Component name="BSFC" unitsValue="" plotLabel="(g/kWh)" id="989" />
<Component name="instantaneous" unitsValue="" plotLabel="(l/s)" id="990" />
<Component name="instantaneous_Liter_100km" unitsValue="" plotLabel="(L / 100km)" id="991" />
<Component name="overall" unitsValue="" plotLabel="(l)" id="992" />
</Entity>
<Entity name="ges_chassis_XFORM" entity="ges_chassis_XFORM" entType="Part">
<Component name="Phi" unitsValue="radian" plotLabel="" id="993" />
<Component name="Psi" unitsValue="radian" plotLabel="" id="994" />
<Component name="Theta" unitsValue="radian" plotLabel="" id="995" />
<Component name="X" unitsValue="meter" plotLabel="" id="996" />
<Component name="Y" unitsValue="meter" plotLabel="" id="997" />
<Component name="Z" unitsValue="meter" plotLabel="" id="998" />
</Entity>
<Entity name="ges_hub_XFORMFL" entity="ges_hub_XFORMFL" entType="Part">
<Component name="X" unitsValue="meter" plotLabel="" id="999" />
<Component name="Y" unitsValue="meter" plotLabel="" id="1000" />
<Component name="Z" unitsValue="meter" plotLabel="" id="1001" />
<Component name="Psi" unitsValue="radian" plotLabel="" id="1002" />
<Component name="Theta" unitsValue="radian" plotLabel="" id="1003" />
<Component name="Phi" unitsValue="radian" plotLabel="" id="1004" />
</Entity>
<Entity name="ges_hub_XFORMFR" entity="ges_hub_XFORMFR" entType="Part">
<Component name="X" unitsValue="meter" plotLabel="" id="1005" />
<Component name="Y" unitsValue="meter" plotLabel="" id="1006" />
<Component name="Z" unitsValue="meter" plotLabel="" id="1007" />
<Component name="Psi" unitsValue="radian" plotLabel="" id="1008" />
<Component name="Theta" unitsValue="radian" plotLabel="" id="1009" />
<Component name="Phi" unitsValue="radian" plotLabel="" id="1010" />
</Entity>
<Entity name="ges_hub_XFORMRL" entity="ges_hub_XFORMRL" entType="Part">
<Component name="X" unitsValue="meter" plotLabel="" id="1011" />
<Component name="Y" unitsValue="meter" plotLabel="" id="1012" />
<Component name="Z" unitsValue="meter" plotLabel="" id="1013" />
<Component name="Psi" unitsValue="radian" plotLabel="" id="1014" />
<Component name="Theta" unitsValue="radian" plotLabel="" id="1015" />
<Component name="Phi" unitsValue="radian" plotLabel="" id="1016" />
</Entity>
<Entity name="ges_hub_XFORMRR" entity="ges_hub_XFORMRR" entType="Part">
<Component name="X" unitsValue="meter" plotLabel="" id="1017" />
<Component name="Y" unitsValue="meter" plotLabel="" id="1018" />
<Component name="Z" unitsValue="meter" plotLabel="" id="1019" />
<Component name="Psi" unitsValue="radian" plotLabel="" id="1020" />
<Component name="Theta" unitsValue="radian" plotLabel="" id="1021" />
<Component name="Phi" unitsValue="radian" plotLabel="" id="1022" />
</Entity>
<Entity name="hub2cp_XFORMFL" entity="hub2cp_XFORMFL" entType="Part">
<Component name="X" unitsValue="meter" plotLabel="" id="1023" />
<Component name="Y" unitsValue="meter" plotLabel="" id="1024" />
<Component name="Z" unitsValue="meter" plotLabel="" id="1025" />
</Entity>
<Entity name="hub2cp_XFORMFR" entity="hub2cp_XFORMFR" entType="Part">
<Component name="X" unitsValue="meter" plotLabel="" id="1026" />
<Component name="Y" unitsValue="meter" plotLabel="" id="1027" />
<Component name="Z" unitsValue="meter" plotLabel="" id="1028" />
</Entity>
<Entity name="hub2cp_XFORMRL" entity="hub2cp_XFORMRL" entType="Part">
<Component name="X" unitsValue="meter" plotLabel="" id="1029" />
<Component name="Y" unitsValue="meter" plotLabel="" id="1030" />
<Component name="Z" unitsValue="meter" plotLabel="" id="1031" />
</Entity>
<Entity name="hub2cp_XFORMRR" entity="hub2cp_XFORMRR" entType="Part">
<Component name="X" unitsValue="meter" plotLabel="" id="1032" />
<Component name="Y" unitsValue="meter" plotLabel="" id="1033" />
<Component name="Z" unitsValue="meter" plotLabel="" id="1034" />
</Entity>
<Entity name="motor_to_clutch" entity="motor_to_clutch" entType="Request">
<Component name="clutch_inputshaft_alpha" unitsValue="radian/second**2" plotLabel="" id="1035" />
<Component name="clutch_inputshaft_angle" unitsValue="radian" plotLabel="" id="1036" />
<Component name="clutch_inputshaft_omega" unitsValue="radian/second" plotLabel="" id="1037" />
<Component name="effective_throttle" unitsValue="" plotLabel="Engine Throttle [0 to 100] (-)" id="1038" />
<Component name="engine_rpm" unitsValue="" plotLabel="(RPM)" id="1039" />
<Component name="Max_Engine_torque" unitsValue="newton-meter" plotLabel="" id="1040" />
<Component name="Min_engine_torque" unitsValue="newton-meter" plotLabel="" id="1041" />
<Component name="Power_KW" unitsValue="" plotLabel="(KW)" id="1042" />
<Component name="TCS_activity" unitsValue="" plotLabel="Traction_Control_Activation (-)" id="1043" />
<Component name="Theoretical_Power_KW" unitsValue="" plotLabel="(KW)" id="1044" />
<Component name="torque" unitsValue="newton-meter" plotLabel="" id="1045" />
<Component name="efficiency" unitsValue="" plotLabel="(efficiency)" id="1046" />
<Component name="Launch_Control_activity" unitsValue="" plotLabel="Launch_Control_Activation (-)" id="1047" />
<Component name="energy_consumption" unitsValue="" plotLabel="(KWh)" id="1048" />
<Component name="transmission_ratio" unitsValue="" plotLabel="(-)" id="1049" />
<Component name="outshaft_torque" unitsValue="newton-meter" plotLabel="" id="1050" />
<Component name="outshaft_power_KW" unitsValue="" plotLabel="(KW)" id="1051" />
</Entity>
<Entity name="nsl_ride_spring_data" entity="nsl_ride_spring_data" entType="Request">
<Component name="displacement_front" unitsValue="meter" plotLabel="" id="1052" />
<Component name="displacement_rear" unitsValue="meter" plotLabel="" id="1053" />
<Component name="force_front" unitsValue="newton" plotLabel="" id="1054" />
<Component name="force_rear" unitsValue="newton" plotLabel="" id="1055" />
<Component name="velocity_front" unitsValue="meter/second" plotLabel="" id="1056" />
<Component name="velocity_rear" unitsValue="meter/second" plotLabel="" id="1057" />
</Entity>
<Entity name="nsr_ride_spring_data" entity="nsr_ride_spring_data" entType="Request">
<Component name="displacement_front" unitsValue="meter" plotLabel="" id="1058" />
<Component name="displacement_rear" unitsValue="meter" plotLabel="" id="1059" />
<Component name="force_front" unitsValue="newton" plotLabel="" id="1060" />
<Component name="force_rear" unitsValue="newton" plotLabel="" id="1061" />
<Component name="velocity_front" unitsValue="meter/second" plotLabel="" id="1062" />
<Component name="velocity_rear" unitsValue="meter/second" plotLabel="" id="1063" />
</Entity>
<Entity name="rhl_front_setup_sensor_data" entity="rhl_front_setup_sensor_data" entType="Request">
<Component name="ride_height" unitsValue="meter" plotLabel="" id="1064" />
</Entity>
<Entity name="rhr_front_setup_sensor_data" entity="rhr_front_setup_sensor_data" entType="Request">
<Component name="ride_height" unitsValue="meter" plotLabel="" id="1065" />
</Entity>
<Entity name="rhs_rear_setup_sensor_data" entity="rhs_rear_setup_sensor_data" entType="Request">
<Component name="ride_height" unitsValue="meter" plotLabel="" id="1066" />
</Entity>
<Entity name="til_wheel_tire_forces" entity="til_wheel_tire_forces" entType="Request">
<Component name="aligning_torque_front" unitsValue="newton-meter" plotLabel="" id="1067" />
<Component name="aligning_torque_rear" unitsValue="newton-meter" plotLabel="" id="1068" />
<Component name="lateral_front" unitsValue="newton" plotLabel="" id="1069" />
<Component name="lateral_rear" unitsValue="newton" plotLabel="" id="1070" />
<Component name="longitudinal_front" unitsValue="newton" plotLabel="" id="1071" />
<Component name="longitudinal_rear" unitsValue="newton" plotLabel="" id="1072" />
<Component name="normal_front" unitsValue="newton" plotLabel="" id="1073" />
<Component name="normal_rear" unitsValue="newton" plotLabel="" id="1074" />
<Component name="overturning_moment_front" unitsValue="newton-meter" plotLabel="" id="1075" />
<Component name="overturning_moment_rear" unitsValue="newton-meter" plotLabel="" id="1076" />
<Component name="rolling_resistance_front" unitsValue="newton-meter" plotLabel="" id="1077" />
<Component name="rolling_resistance_rear" unitsValue="newton-meter" plotLabel="" id="1078" />
</Entity>
<Entity name="til_wheel_tire_kinematics" entity="til_wheel_tire_kinematics" entType="Request">
<Component name="inclination_angle_front" unitsValue="radian" plotLabel="" id="1079" />
<Component name="inclination_angle_rear" unitsValue="radian" plotLabel="" id="1080" />
<Component name="lateral_slip_front" unitsValue="radian" plotLabel="" id="1081" />
<Component name="lateral_slip_rear" unitsValue="radian" plotLabel="" id="1082" />
<Component name="longitudinal_slip_front" unitsValue="" plotLabel="Percent Longitudinal Slip [-100 = lockup]" id="1083" />
<Component name="longitudinal_slip_rear" unitsValue="" plotLabel="Percent Longitudinal Slip [-100 = lockup]" id="1084" />
</Entity>
<Entity name="til_wheel_tire_rolling_states" entity="til_wheel_tire_rolling_states" entType="Request">
<Component name="omega_actual_front" unitsValue="radian/second" plotLabel="" id="1085" />
<Component name="omega_actual_rear" unitsValue="radian/second" plotLabel="" id="1086" />
<Component name="omega_free_front" unitsValue="radian/second" plotLabel="" id="1087" />
<Component name="omega_free_rear" unitsValue="radian/second" plotLabel="" id="1088" />
<Component name="rolling_radius_front" unitsValue="meter" plotLabel="" id="1089" />
<Component name="rolling_radius_rear" unitsValue="meter" plotLabel="" id="1090" />
</Entity>
<Entity name="tir_wheel_tire_forces" entity="tir_wheel_tire_forces" entType="Request">
<Component name="aligning_torque_front" unitsValue="newton-meter" plotLabel="" id="1091" />
<Component name="aligning_torque_rear" unitsValue="newton-meter" plotLabel="" id="1092" />
<Component name="lateral_front" unitsValue="newton" plotLabel="" id="1093" />
<Component name="lateral_rear" unitsValue="newton" plotLabel="" id="1094" />
<Component name="longitudinal_front" unitsValue="newton" plotLabel="" id="1095" />
<Component name="longitudinal_rear" unitsValue="newton" plotLabel="" id="1096" />
<Component name="normal_front" unitsValue="newton" plotLabel="" id="1097" />
<Component name="normal_rear" unitsValue="newton" plotLabel="" id="1098" />
<Component name="overturning_moment_front" unitsValue="newton-meter" plotLabel="" id="1099" />
<Component name="overturning_moment_rear" unitsValue="newton-meter" plotLabel="" id="1100" />
<Component name="rolling_resistance_front" unitsValue="newton-meter" plotLabel="" id="1101" />
<Component name="rolling_resistance_rear" unitsValue="newton-meter" plotLabel="" id="1102" />
</Entity>
<Entity name="tir_wheel_tire_kinematics" entity="tir_wheel_tire_kinematics" entType="Request">
<Component name="inclination_angle_front" unitsValue="radian" plotLabel="" id="1103" />
<Component name="inclination_angle_rear" unitsValue="radian" plotLabel="" id="1104" />
<Component name="lateral_slip_front" unitsValue="radian" plotLabel="" id="1105" />
<Component name="lateral_slip_rear" unitsValue="radian" plotLabel="" id="1106" />
<Component name="longitudinal_slip_front" unitsValue="" plotLabel="Percent Longitudinal Slip [-100 = lockup]" id="1107" />
<Component name="longitudinal_slip_rear" unitsValue="" plotLabel="Percent Longitudinal Slip [-100 = lockup]" id="1108" />
</Entity>
<Entity name="tir_wheel_tire_rolling_states" entity="tir_wheel_tire_rolling_states" entType="Request">
<Component name="omega_actual_front" unitsValue="radian/second" plotLabel="" id="1109" />
<Component name="omega_actual_rear" unitsValue="radian/second" plotLabel="" id="1110" />
<Component name="omega_free_front" unitsValue="radian/second" plotLabel="" id="1111" />
<Component name="omega_free_rear" unitsValue="radian/second" plotLabel="" id="1112" />
<Component name="rolling_radius_front" unitsValue="meter" plotLabel="" id="1113" />
<Component name="rolling_radius_rear" unitsValue="meter" plotLabel="" id="1114" />
</Entity>
<Entity name="transmission" entity="transmission" entType="Request">
<Component name="automatic_gearbox_shifting_mode" unitsValue="" plotLabel="" id="1115" />
<Component name="clutch_outputplate_torque" unitsValue="newton*meter" plotLabel="" id="1116" />
<Component name="diff_central_inputshaft_alpha" unitsValue="radian/second**2" plotLabel="" id="1117" />
<Component name="diff_central_inputshaft_angle" unitsValue="radian" plotLabel="" id="1118" />
<Component name="diff_central_inputshaft_omega" unitsValue="radian/second" plotLabel="" id="1119" />
<Component name="gear" unitsValue="" plotLabel="" id="1120" />
<Component name="input_rpm" unitsValue="" plotLabel="(RPM)" id="1121" />
<Component name="output_rpm" unitsValue="" plotLabel="(RPM)" id="1122" />
<Component name="ratio" unitsValue="" plotLabel="" id="1123" />
<Component name="torque" unitsValue="newton-meter" plotLabel="" id="1124" />
<Component name="manual_shifting_activity" unitsValue="" plotLabel="(Activation)" id="1125" />
</Entity>
<Entity name="upright_accelerometer" entity="upright_accelerometer" entType="Request">
<Component name="Z_left_front" unitsValue="meter/second**2" plotLabel="" id="1126" />
<Component name="Z_left_rear" unitsValue="meter/second**2" plotLabel="" id="1127" />
<Component name="Z_right_front" unitsValue="meter/second**2" plotLabel="" id="1128" />
<Component name="Z_right_rear" unitsValue="meter/second**2" plotLabel="" id="1129" />
</Entity>
<Entity name="vel_sensor" entity="vel_sensor" entType="Request">
<Component name="VX" unitsValue="meter/second" plotLabel="" id="1130" />
<Component name="VY" unitsValue="meter/second" plotLabel="" id="1131" />
<Component name="VZ" unitsValue="meter/second" plotLabel="" id="1132" />
</Entity>
<Entity name="wheel_angles" entity="wheel_angles" entType="Request">
<Component name="camber_L1" unitsValue="radian" plotLabel="" id="1133" />
<Component name="camber_L2" unitsValue="radian" plotLabel="" id="1134" />
<Component name="camber_R1" unitsValue="radian" plotLabel="" id="1135" />
<Component name="camber_R2" unitsValue="radian" plotLabel="" id="1136" />
<Component name="camber_wrt_road_L1" unitsValue="radian" plotLabel="" id="1137" />
<Component name="camber_wrt_road_L2" unitsValue="radian" plotLabel="" id="1138" />
<Component name="camber_wrt_road_R1" unitsValue="radian" plotLabel="" id="1139" />
<Component name="camber_wrt_road_R2" unitsValue="radian" plotLabel="" id="1140" />
<Component name="caster_L1" unitsValue="radian" plotLabel="" id="1141" />
<Component name="caster_L2" unitsValue="radian" plotLabel="" id="1142" />
<Component name="caster_R1" unitsValue="radian" plotLabel="" id="1143" />
<Component name="caster_R2" unitsValue="radian" plotLabel="" id="1144" />
<Component name="caster_wrt_road_L1" unitsValue="radian" plotLabel="" id="1145" />
<Component name="caster_wrt_road_L2" unitsValue="radian" plotLabel="" id="1146" />
<Component name="caster_wrt_road_R1" unitsValue="radian" plotLabel="" id="1147" />
<Component name="caster_wrt_road_R2" unitsValue="radian" plotLabel="" id="1148" />
<Component name="toe_L1" unitsValue="radian" plotLabel="" id="1149" />
<Component name="toe_L2" unitsValue="radian" plotLabel="" id="1150" />
<Component name="toe_R1" unitsValue="radian" plotLabel="" id="1151" />
<Component name="toe_R2" unitsValue="radian" plotLabel="" id="1152" />
<Component name="toe_wrt_road_L1" unitsValue="radian" plotLabel="" id="1153" />
<Component name="toe_wrt_road_L2" unitsValue="radian" plotLabel="" id="1154" />
<Component name="toe_wrt_road_R1" unitsValue="radian" plotLabel="" id="1155" />
<Component name="toe_wrt_road_R2" unitsValue="radian" plotLabel="" id="1156" />
</Entity>
<Entity name="whl_front_wheel_XFORM" entity="whl_front_wheel_XFORM" entType="Force">
<Component name="FX" unitsValue="newton" plotLabel="" id="1157" />
<Component name="FY" unitsValue="newton" plotLabel="" id="1158" />
<Component name="FZ" unitsValue="newton" plotLabel="" id="1159" />
<Component name="Phi" unitsValue="radian" plotLabel="" id="1160" />
<Component name="Psi" unitsValue="radian" plotLabel="" id="1161" />
<Component name="Theta" unitsValue="radian" plotLabel="" id="1162" />
<Component name="X" unitsValue="meter" plotLabel="" id="1163" />
<Component name="Y" unitsValue="meter" plotLabel="" id="1164" />
<Component name="Z" unitsValue="meter" plotLabel="" id="1165" />
</Entity>
<Entity name="whl_rear_wheel_XFORM" entity="whl_rear_wheel_XFORM" entType="Force">
<Component name="FX" unitsValue="newton" plotLabel="" id="1166" />
<Component name="FY" unitsValue="newton" plotLabel="" id="1167" />
<Component name="FZ" unitsValue="newton" plotLabel="" id="1168" />
<Component name="Phi" unitsValue="radian" plotLabel="" id="1169" />
<Component name="Psi" unitsValue="radian" plotLabel="" id="1170" />
<Component name="Theta" unitsValue="radian" plotLabel="" id="1171" />
<Component name="X" unitsValue="meter" plotLabel="" id="1172" />
<Component name="Y" unitsValue="meter" plotLabel="" id="1173" />
<Component name="Z" unitsValue="meter" plotLabel="" id="1174" />
</Entity>
<Entity name="whl_twin_rear_wheel_XFORM" entity="whl_twin_rear_wheel_XFORM" entType="Force">
<Component name="FX" unitsValue="newton" plotLabel="" id="1175" />
<Component name="FY" unitsValue="newton" plotLabel="" id="1176" />
<Component name="FZ" unitsValue="newton" plotLabel="" id="1177" />
<Component name="Phi" unitsValue="radian" plotLabel="" id="1178" />
<Component name="Psi" unitsValue="radian" plotLabel="" id="1179" />
<Component name="Theta" unitsValue="radian" plotLabel="" id="1180" />
<Component name="X" unitsValue="meter" plotLabel="" id="1181" />
<Component name="Y" unitsValue="meter" plotLabel="" id="1182" />
<Component name="Z" unitsValue="meter" plotLabel="" id="1183" />
</Entity>
<Entity name="whr_front_wheel_XFORM" entity="whr_front_wheel_XFORM" entType="Force">
<Component name="FX" unitsValue="newton" plotLabel="" id="1184" />
<Component name="FY" unitsValue="newton" plotLabel="" id="1185" />
<Component name="FZ" unitsValue="newton" plotLabel="" id="1186" />
<Component name="Phi" unitsValue="radian" plotLabel="" id="1187" />
<Component name="Psi" unitsValue="radian" plotLabel="" id="1188" />
<Component name="Theta" unitsValue="radian" plotLabel="" id="1189" />
<Component name="X" unitsValue="meter" plotLabel="" id="1190" />
<Component name="Y" unitsValue="meter" plotLabel="" id="1191" />
<Component name="Z" unitsValue="meter" plotLabel="" id="1192" />
</Entity>
<Entity name="whr_rear_wheel_XFORM" entity="whr_rear_wheel_XFORM" entType="Force">
<Component name="FX" unitsValue="newton" plotLabel="" id="1193" />
<Component name="FY" unitsValue="newton" plotLabel="" id="1194" />
<Component name="FZ" unitsValue="newton" plotLabel="" id="1195" />
<Component name="Phi" unitsValue="radian" plotLabel="" id="1196" />
<Component name="Psi" unitsValue="radian" plotLabel="" id="1197" />
<Component name="Theta" unitsValue="radian" plotLabel="" id="1198" />
<Component name="X" unitsValue="meter" plotLabel="" id="1199" />
<Component name="Y" unitsValue="meter" plotLabel="" id="1200" />
<Component name="Z" unitsValue="meter" plotLabel="" id="1201" />
</Entity>
<Entity name="whr_twin_rear_wheel_XFORM" entity="whr_twin_rear_wheel_XFORM" entType="Force">
<Component name="FX" unitsValue="newton" plotLabel="" id="1202" />
<Component name="FY" unitsValue="newton" plotLabel="" id="1203" />
<Component name="FZ" unitsValue="newton" plotLabel="" id="1204" />
<Component name="Phi" unitsValue="radian" plotLabel="" id="1205" />
<Component name="Psi" unitsValue="radian" plotLabel="" id="1206" />
<Component name="Theta" unitsValue="radian" plotLabel="" id="1207" />
<Component name="X" unitsValue="meter" plotLabel="" id="1208" />
<Component name="Y" unitsValue="meter" plotLabel="" id="1209" />
<Component name="Z" unitsValue="meter" plotLabel="" id="1210" />
</Entity>
</StepMap>
<TerminationStatus runTermObject="" runStatus="0" />
</Analysis>
</Results>
