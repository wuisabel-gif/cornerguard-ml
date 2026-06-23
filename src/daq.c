#include "daq.h"

static DAQ_Status_TypeDef packImuPayload(const ImuSensor *sensor,
                                         IMU_Data_TypeDef data_type,
                                         uint8_t data[8])
{
  if (sensor->broke)
  {
    return data_type == ACCEL ? ACCEL_ERROR : GYRO_ERROR;
  }

  data[0] = (uint8_t)data_type;
  data[1] = sensor->x.low;
  data[2] = sensor->x.high;
  data[3] = sensor->y.low;
  data[4] = sensor->y.high;
  data[5] = sensor->z.low;
  data[6] = sensor->z.high;
  data[7] = 0U;

  return DAQ_OK;
}

void initCompleteFlash(void)
{
  HAL_Delay(500);
  for (uint8_t i = 0U; i < 6U; i++)
  {
    HAL_GPIO_TogglePin(LD3_GPIO_Port, LD3_Pin);
    HAL_Delay(150);
  }
}

DAQ_Status_TypeDef daqInit(I2C_HandleTypeDef *hi2c, CAN_HandleTypeDef *hcan,
                           DAQ_TypeDef *daq)
{
  daq->hcan = hcan;

  if (imuInit(&(daq->imu), hi2c) != HAL_OK)
  {
    return IMU_ERROR;
  }

  if (HAL_CAN_Start(daq->hcan) != HAL_OK)
  {
    return CAN_ERROR;
  }

  return DAQ_OK;
}

DAQ_Status_TypeDef daqReadData(DAQ_TypeDef *daq)
{
  IMU_t *imu = &(daq->imu);
  ImuSensor *accel = &(imu->accelerometer);
  ImuSensor *gyro = &(imu->gyro);
  I2C_HandleTypeDef *hi2c = imu->i2c;

  if (readAccel(accel, hi2c) != HAL_OK)
  {
    return ACCEL_ERROR;
  }

  if (readGyro(gyro, hi2c) != HAL_OK)
  {
    return GYRO_ERROR;
  }

  return DAQ_OK;
}

DAQ_Status_TypeDef daqSendImuData(DAQ_TypeDef *daq, IMU_Data_TypeDef data_type)
{
  uint32_t mailbox;
  uint32_t start_tick;
  uint8_t data[8] = {0};
  DAQ_Status_TypeDef pack_status;

  CAN_TxHeaderTypeDef header;
  header.StdId = IMU_ADDR;
  header.IDE = CAN_ID_STD;
  header.RTR = CAN_RTR_DATA;
  header.DLC = 8;
  header.TransmitGlobalTime = DISABLE;

  switch (data_type)
  {
    case ACCEL:
      pack_status = packImuPayload(&(daq->imu.accelerometer), data_type, data);
      break;
    case GYRO:
      pack_status = packImuPayload(&(daq->imu.gyro), data_type, data);
      break;
    default:
      return GENERIC_ERROR;
  }

  if (pack_status != DAQ_OK)
  {
    return pack_status;
  }

  start_tick = HAL_GetTick();
  while (HAL_CAN_GetTxMailboxesFreeLevel(daq->hcan) == 0U)
  {
    if ((HAL_GetTick() - start_tick) >= DAQ_CAN_TX_TIMEOUT_MS)
    {
      return CAN_ERROR;
    }
  }

  if (HAL_CAN_AddTxMessage(daq->hcan, &header, data, &mailbox) != HAL_OK)
  {
    return CAN_ERROR;
  }

  return DAQ_OK;
}
