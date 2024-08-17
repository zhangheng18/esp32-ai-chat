"""
    dht20 python驱动 由ChatGPT生成
"""

import time


class DHT20:
    def __init__(self, i2c, address=0x38):
        self.i2c = i2c
        self.address = address
        self._temperature = None
        self._humidity = None

    def measure(self):
        try:
            self.i2c.writeto(self.address, b'\xAC\x33\x00')
            time.sleep_ms(50)  # Wait for measurement
            data = self.i2c.readfrom(self.address, 7)
            if data[0] & 0x80:
                print("Sensor busy, retrying...")
                return None
            self._humidity = (
                ((data[1] << 12) | (data[2] << 4) | (data[3] >> 4)) * 100 / 2**20
            )
            self._temperature = (
                ((data[3] & 0xF) << 16) | (data[4] << 8) | data[5]
            ) * 200 / 2**20 - 50
            return self._humidity and self._temperature
        except OSError as e:
            print("Error during data read:", e)
            return None

    def humidity(self):
        return self._humidity

    def temperature(self):
        return self._temperature

        def __str__(self):
            return f"Temperature: {self._temperature:.1f}°C, Humidity: {self._humidity:.1f}%"


if __name__ == "__main__":
    from machine import I2C, Pin

    i2c = I2C(scl=Pin(22), sda=Pin(21))
    dht = DHT20(i2c)
    if dht.measure():
        print(
            'Temperature: {:.2f} C, Humidity: {:.2f} %'.format(
                dht.temperature(), dht.humidity()
            )
        )
