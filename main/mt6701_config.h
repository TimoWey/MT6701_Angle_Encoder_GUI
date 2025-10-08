#ifndef MT6701_CONFIG_H
#define MT6701_CONFIG_H

// I2C Configuration for XIAO ESP32-C3
// SDA = D4 (GPIO6), SCL = D5 (GPIO7)
#define I2C_MASTER_SCL_IO      7       // SCL pin (D5 / GPIO7)
#define I2C_MASTER_SDA_IO      6       // SDA pin (D4 / GPIO6)
#define I2C_MASTER_NUM         I2C_NUM_0
#define I2C_MASTER_FREQ_HZ     4000  // 400kHz I2C frequency
#define I2C_MASTER_TX_BUF_DISABLE 0
#define I2C_MASTER_RX_BUF_DISABLE 0

// MT6701 Configuration
#define MT6701_I2C_ADDR        0x06    // Default I2C address
#define MT6701_ANGLE_REG       0x03    // 14-bit angle register
#define MT6701_READ_TIMEOUT_MS 1000    // I2C read timeout

// Update settings
#define ENCODER_UPDATE_MS      100     // Update frequency in milliseconds
#define SERIAL_BAUD_RATE       115200  // Serial monitor baud rate

// Debug settings
#define DEBUG_ENABLED          1       // Enable debug output

#endif // MT6701_CONFIG_H
