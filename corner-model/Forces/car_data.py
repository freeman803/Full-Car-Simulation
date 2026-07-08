class CarData:
    """
    A class to hold general information about the car.
    """
    MASS_KG = 200
    CG_HEIGHT_MM = 315
    FRONT_TRACK_MM = 1219
    REAR_TRACK_MM = 1168
    WHEELBASE_MM = 1545
    TOTAL_DOWNFORCE_N = 477
    CENTER_OF_PRESSURE = 0.3801
    CENTER_OF_MASS = 0.5

    @classmethod
    def get_data(cls):
        return {
            "mass_kg": cls.MASS_KG,
            "cg_height_mm": cls.CG_HEIGHT_MM,
            "front_track_mm": cls.FRONT_TRACK_MM,
            "rear_track_mm": cls.REAR_TRACK_MM,
            "wheelbase_mm": cls.WHEELBASE_MM,
            "total_downforce_N": cls.TOTAL_DOWNFORCE_N,
            "center_of_pressure": cls.CENTER_OF_PRESSURE,
        }

    @classmethod
    def print_data(cls):
        print("Car General Information:")
        for key, value in cls.get_data().items():
            print(f"- {key.replace('_', ' ').title()}: {value}")

if __name__ == "__main__":
    CarData.print_data()
