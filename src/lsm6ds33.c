#include "lsm6ds33.h"

#define ACCEL_DATARATE ACCEL_DR_104_Hz
#define ACCEL_RANGE    ACCEL_4G
#define GYRO_DATARATE  GYRO_DR_104_Hz
#define GYRO_RANGE     FS_245_DPS

#define LSM6DS33_REG_ADDR_SIZE 1U
#define LSM6DS33_I2C_TIMEOUT_MS 100U
#define MDPS_TO_DPS 0.001F
#define MG_TO_G 0.001F

static float gyroScaleDpsPerLsb(GYRO_FULL_SCALE full_scale)
{
  switch (full_scale)
  {
    case FS_245_DPS:
      return 8.75F * MDPS_TO_DPS;
    case FS_500_DPS:
      return 17.5F * MDPS_TO_DPS;
    case FS_1000_DPS:
      return 35.0F * MDPS_TO_DPS;
    case FS_2000_DPS:
      return 70.0F * MDPS_TO_DPS;
    default:
      return 8.75F * MDPS_TO_DPS;
  }
}

static float accelScaleGPerLsb(ACCEL_FS full_scale)
{
  switch (full_scale)
  {
    case ACCEL_2G:
      return 0.061F * MG_TO_G;
    case ACCEL_4G:
      return 0.122F * MG_TO_G;
    case ACCEL_8G:
      return 0.244F * MG_TO_G;
    case ACCEL_16G:
      return 0.488F * MG_TO_G;
    default:
      return 0.122F * MG_TO_G;
  }
}

static HAL_StatusTypeDef readRegister(I2C_HandleTypeDef *hi2c,
                                      uint8_t address,
                                      uint8_t *value)
{
  return HAL_I2C_Mem_Read(hi2c,
                          LSM6DS33_ADDR,
                          address,
                          LSM6DS33_REG_ADDR_SIZE,
                          value,
                          1U,
                          LSM6DS33_I2C_TIMEOUT_MS);
}

static HAL_StatusTypeDef writeRegister(I2C_HandleTypeDef *hi2c,
                                       uint8_t address,
                                       uint8_t value)
{
  return HAL_I2C_Mem_Write(hi2c,
                           LSM6DS33_ADDR,
                           address,
                           LSM6DS33_REG_ADDR_SIZE,
                           &value,
                           1U,
                           LSM6DS33_I2C_TIMEOUT_MS);
}

static HAL_StatusTypeDef readAxis(I2C_HandleTypeDef *hi2c,
                                  uint8_t high_addr,
                                  uint8_t low_addr,
                                  AxisData_t *axis)
{
  HAL_StatusTypeDef status;

  status = readRegister(hi2c, high_addr, &(axis->high));
  if (status != HAL_OK)
  {
    return status;
  }

  return readRegister(hi2c, low_addr, &(axis->low));
}

static HAL_StatusTypeDef readSensorAxes(ImuSensor *sensor,
                                        I2C_HandleTypeDef *hi2c,
                                        uint8_t x_high_addr,
                                        uint8_t x_low_addr,
                                        uint8_t y_high_addr,
                                        uint8_t y_low_addr,
                                        uint8_t z_high_addr,
                                        uint8_t z_low_addr)
{
  HAL_StatusTypeDef status;

  status = readAxis(hi2c, x_high_addr, x_low_addr, &(sensor->x));
  if (status != HAL_OK)
  {
    sensor->broke = 1U;
    return status;
  }

  status = readAxis(hi2c, y_high_addr, y_low_addr, &(sensor->y));
  if (status != HAL_OK)
  {
    sensor->broke = 1U;
    return status;
  }

  status = readAxis(hi2c, z_high_addr, z_low_addr, &(sensor->z));
  if (status != HAL_OK)
  {
    sensor->broke = 1U;
    return status;
  }

  sensor->broke = 0U;
  return HAL_OK;
}

HAL_StatusTypeDef gyroInit(IMU_t *imu,
                           GYRO_DATA_RATE data_rate,
                           GYRO_FULL_SCALE full_scale,
                           int high_pass_filter)
{
  HAL_StatusTypeDef status;
  ImuSensor *gyro = &(imu->gyro);
  uint8_t ctrl2_g = (uint8_t)((data_rate << 4) | (full_scale << 2));

  status = HAL_I2C_IsDeviceReady(imu->i2c,
                                 LSM6DS33_ADDR,
                                 2U,
                                 LSM6DS33_I2C_TIMEOUT_MS);
  if (status != HAL_OK)
  {
    gyro->broke = 1U;
    return status;
  }

  gyro->conversion = gyroScaleDpsPerLsb(full_scale);

  status = writeRegister(imu->i2c, CTRL2_G, ctrl2_g);
  if (status != HAL_OK)
  {
    gyro->broke = 1U;
    return status;
  }

  if (high_pass_filter)
  {
    status = writeRegister(imu->i2c, CTRL7_G, (uint8_t)(0x01U << 6));
    if (status != HAL_OK)
    {
      gyro->broke = 1U;
      return status;
    }
  }

  gyro->broke = 0U;
  return HAL_OK;
}

HAL_StatusTypeDef readGyro(ImuSensor *gyro, I2C_HandleTypeDef *hi2c)
{
  return readSensorAxes(gyro,
                        hi2c,
                        OUTX_H_G,
                        OUTX_L_G,
                        OUTY_H_G,
                        OUTY_L_G,
                        OUTZ_H_G,
                        OUTZ_L_G);
}

HAL_StatusTypeDef accelInit(IMU_t *imu, ACCEL_DATA_RATE data_rate, ACCEL_FS full_scale)
{
  HAL_StatusTypeDef status;
  ImuSensor *accel = &(imu->accelerometer);
  uint8_t ctrl1_xl = (uint8_t)((data_rate << 4) | (full_scale << 2));

  status = HAL_I2C_IsDeviceReady(imu->i2c,
                                 LSM6DS33_ADDR,
                                 2U,
                                 LSM6DS33_I2C_TIMEOUT_MS);
  if (status != HAL_OK)
  {
    accel->broke = 1U;
    return status;
  }

  accel->conversion = accelScaleGPerLsb(full_scale);

  status = writeRegister(imu->i2c, CTRL1_XL, ctrl1_xl);
  if (status != HAL_OK)
  {
    accel->broke = 1U;
    return status;
  }

  accel->broke = 0U;
  return HAL_OK;
}

HAL_StatusTypeDef readAccel(ImuSensor *accel, I2C_HandleTypeDef *hi2c)
{
  return readSensorAxes(accel,
                        hi2c,
                        OUTX_H_XL,
                        OUTX_L_XL,
                        OUTY_H_XL,
                        OUTY_L_XL,
                        OUTZ_H_XL,
                        OUTZ_L_XL);
}

HAL_StatusTypeDef imuInit(IMU_t *imu, I2C_HandleTypeDef *hi2c)
{
  HAL_StatusTypeDef status;

  imu->i2c = hi2c;

  status = accelInit(imu, ACCEL_DATARATE, ACCEL_RANGE);
  if (status != HAL_OK)
  {
    return status;
  }

  status = gyroInit(imu, GYRO_DATARATE, GYRO_RANGE, 0);
  if (status != HAL_OK)
  {
    return status;
  }

  return HAL_OK;
}
