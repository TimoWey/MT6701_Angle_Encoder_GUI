#include <stdio.h>
#include <string.h>
#include <math.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/i2c.h"
#include "esp_log.h"
#include "esp_err.h"
#include "mt6701_config.h"

static const char *TAG = "MT6701";

// I2C initialization
esp_err_t i2c_master_init(void)
{
    int i2c_master_port = I2C_MASTER_NUM;

    i2c_config_t conf = {
        .mode = I2C_MODE_MASTER,
        .sda_io_num = I2C_MASTER_SDA_IO,
        .scl_io_num = I2C_MASTER_SCL_IO,
        .sda_pullup_en = GPIO_PULLUP_ENABLE,
        .scl_pullup_en = GPIO_PULLUP_ENABLE,
        .master.clk_speed = I2C_MASTER_FREQ_HZ,
    };

    i2c_param_config(i2c_master_port, &conf);

    return i2c_driver_install(i2c_master_port, conf.mode, I2C_MASTER_RX_BUF_DISABLE, I2C_MASTER_TX_BUF_DISABLE, 0);
}

// Read 14-bit angle data from MT6701
esp_err_t mt6701_read_angle(float *angle_degrees, uint16_t *raw_out)
{
    uint8_t data[2];
    i2c_cmd_handle_t cmd = i2c_cmd_link_create();
    
    // Start condition
    i2c_master_start(cmd);
    // Write device address + register address
    i2c_master_write_byte(cmd, (MT6701_I2C_ADDR << 1) | I2C_MASTER_WRITE, true);
    i2c_master_write_byte(cmd, MT6701_ANGLE_REG, true);
    // Repeated start condition
    i2c_master_start(cmd);
    // Read device address + read bit
    i2c_master_write_byte(cmd, (MT6701_I2C_ADDR << 1) | I2C_MASTER_READ, true);
    // Read 2 bytes of data
    i2c_master_read_byte(cmd, &data[0], I2C_MASTER_ACK);
    i2c_master_read_byte(cmd, &data[1], I2C_MASTER_NACK);
    // Stop condition
    i2c_master_stop(cmd);
    
    esp_err_t ret = i2c_master_cmd_begin(I2C_MASTER_NUM, cmd, MT6701_READ_TIMEOUT_MS / portTICK_PERIOD_MS);
    i2c_cmd_link_delete(cmd);
    
    if (ret == ESP_OK) {
        // Combine the two bytes to get 14-bit value
        uint16_t raw_angle = ((data[0] & 0x3F) << 8) | data[1];
        
        // Convert to degrees (14-bit = 16384 steps, 360 degrees)
        *angle_degrees = (float)raw_angle * 360.0f / 16384.0f;
        if (raw_out) {
            *raw_out = raw_angle;
        }
        
        #if DEBUG_ENABLED
        ESP_LOGD(TAG, "Raw data: 0x%02X%02X, Raw angle: %d, Degrees: %.2f", 
                 data[0], data[1], raw_angle, *angle_degrees);
        #endif
    }
    
    return ret;
}

// Main task to continuously read and display angle
void mt6701_task(void *pvParameters)
{
    float angle_degrees = 0.0f;
    uint16_t raw_angle = 0;
    esp_err_t ret;
    // Unwrap electrical angle and compute mechanical angle for P=4
    static float previous_angle_deg = 0.0f;
    static int32_t wrap_count = 0;
    
    ESP_LOGI(TAG, "Starting MT6701 angle reading task");
    
    while (1) {
        ret = mt6701_read_angle(&angle_degrees, &raw_angle);
        
        if (ret == ESP_OK) {
            // Detect wraps of electrical angle
            float delta = angle_degrees - previous_angle_deg;
            if (delta > 180.0f) {
                wrap_count--; // crossed 360 -> 0
            } else if (delta < -180.0f) {
                wrap_count++; // crossed 0 -> 360
            }
            previous_angle_deg = angle_degrees;

            // Unwrapped electrical angle and mechanical scaling by measured pole pairs
            const float pole_pairs = 4.0f; // determined from observation
            float unwrapped_electrical_deg = angle_degrees + (float)wrap_count * 360.0f;
            float mechanical_deg = unwrapped_electrical_deg / pole_pairs;
            // Normalize mechanical angle to [0, 360)
            if (mechanical_deg < 0.0f) {
                mechanical_deg += 360.0f * ceilf(-mechanical_deg / 360.0f);
            } else if (mechanical_deg >= 360.0f) {
                mechanical_deg = fmodf(mechanical_deg, 360.0f);
            }

            printf("Raw: %u | Elec: %.2f deg | Mech: %.2f deg | %.2f rad\n",
                   (unsigned)raw_angle, angle_degrees, mechanical_deg, mechanical_deg * M_PI / 180.0f);
        } else {
            ESP_LOGE(TAG, "Failed to read angle from MT6701: %s", esp_err_to_name(ret));
        }
        
        vTaskDelay(pdMS_TO_TICKS(ENCODER_UPDATE_MS));
    }
}

void app_main(void)
{
    ESP_LOGI(TAG, "MT6701 Angle Encoder Reader Starting...");
    
    // Initialize I2C
    esp_err_t ret = i2c_master_init();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "I2C initialization failed: %s", esp_err_to_name(ret));
        return;
    }
    ESP_LOGI(TAG, "I2C initialized successfully");
    
    // Print configuration
    ESP_LOGI(TAG, "Configuration:");
    ESP_LOGI(TAG, "  SCL Pin: %d", I2C_MASTER_SCL_IO);
    ESP_LOGI(TAG, "  SDA Pin: %d", I2C_MASTER_SDA_IO);
    ESP_LOGI(TAG, "  I2C Address: 0x%02X", MT6701_I2C_ADDR);
    ESP_LOGI(TAG, "  Update Rate: %d ms", ENCODER_UPDATE_MS);
    
    // Create task for reading angle
    xTaskCreate(mt6701_task, "mt6701_task", 4096, NULL, 5, NULL);
    
    ESP_LOGI(TAG, "Application started. Check serial output for angle readings.");
}
