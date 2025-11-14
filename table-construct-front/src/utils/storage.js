/**
 * 存储工具函数
 * 提供 localStorage 和 sessionStorage 的统一封装
 */

/**
 * 表格ID存储键名常量
 */
export const TABLE_IDS_KEY = 'table_ids'
export const TABLE_ORDER_KEY = 'table_order'

/**
 * 存储类型枚举
 */
const StorageType = {
  LOCAL: 'localStorage',
  SESSION: 'sessionStorage'
}

/**
 * 获取存储对象实例
 * @param {string} type - 存储类型 'localStorage' 或 'sessionStorage'
 * @returns {Storage} 存储对象
 */
function getStorageInstance(type) {
  try {
    if (type === StorageType.LOCAL) {
      return window.localStorage
    } else if (type === StorageType.SESSION) {
      return window.sessionStorage
    }
    return window.sessionStorage
  } catch (error) {
    console.error('Storage access error:', error)
    return null
  }
}

/**
 * 设置存储项
 * @param {string} key - 键名
 * @param {*} value - 值（可以是对象、数组等）
 * @param {string} type - 存储类型，默认为 'sessionStorage'
 * @returns {boolean} 是否设置成功
 */
export function setStorage(key, value, type = StorageType.SESSION) {
  try {
    const storage = getStorageInstance(type)
    if (!storage) {
      return false
    }
    const stringValue = JSON.stringify(value)
    storage.setItem(key, stringValue)
    return true
  } catch (error) {
    console.error('Set storage error:', error)
    return false
  }
}

/**
 * 获取存储项
 * @param {string} key - 键名
 * @param {*} defaultValue - 默认值（当键不存在时返回）
 * @param {string} type - 存储类型，默认为 'sessionStorage'
 * @returns {*} 存储的值或默认值
 */
export function getStorage(key, defaultValue = null, type = StorageType.SESSION) {
  try {
    const storage = getStorageInstance(type)
    if (!storage) {
      return defaultValue
    }
    const value = storage.getItem(key)
    if (value === null || value === undefined) {
      return defaultValue
    }
    return JSON.parse(value)
  } catch (error) {
    console.error('Get storage error:', error)
    return defaultValue
  }
}

/**
 * 移除存储项
 * @param {string} key - 键名
 * @param {string} type - 存储类型，默认为 'sessionStorage'
 * @returns {boolean} 是否移除成功
 */
export function removeStorage(key, type = StorageType.SESSION) {
  try {
    const storage = getStorageInstance(type)
    if (!storage) {
      return false
    }
    storage.removeItem(key)
    return true
  } catch (error) {
    console.error('Remove storage error:', error)
    return false
  }
}

/**
 * 清空存储
 * @param {string} type - 存储类型，默认为 'sessionStorage'
 * @returns {boolean} 是否清空成功
 */
export function clearStorage(type = StorageType.SESSION) {
  try {
    const storage = getStorageInstance(type)
    if (!storage) {
      return false
    }
    storage.clear()
    return true
  } catch (error) {
    console.error('Clear storage error:', error)
    return false
  }
}

/**
 * 检查存储项是否存在
 * @param {string} key - 键名
 * @param {string} type - 存储类型，默认为 'sessionStorage'
 * @returns {boolean} 是否存在
 */
export function hasStorage(key, type = StorageType.SESSION) {
  try {
    const storage = getStorageInstance(type)
    if (!storage) {
      return false
    }
    return storage.getItem(key) !== null
  } catch (error) {
    console.error('Has storage error:', error)
    return false
  }
}

/**
 * 获取所有存储项的键名
 * @param {string} type - 存储类型，默认为 'sessionStorage'
 * @returns {Array<string>} 键名数组
 */
export function getAllKeys(type = StorageType.SESSION) {
  try {
    const storage = getStorageInstance(type)
    if (!storage) {
      return []
    }
    const keys = []
    for (let i = 0; i < storage.length; i++) {
      keys.push(storage.key(i))
    }
    return keys
  } catch (error) {
    console.error('Get all keys error:', error)
    return []
  }
}

/**
 * 获取存储项的数量
 * @param {string} type - 存储类型，默认为 'sessionStorage'
 * @returns {number} 存储项数量
 */
export function getStorageSize(type = StorageType.SESSION) {
  try {
    const storage = getStorageInstance(type)
    if (!storage) {
      return 0
    }
    return storage.length
  } catch (error) {
    console.error('Get storage size error:', error)
    return 0
  }
}

// 导出存储类型常量
export { StorageType }


/**
 * 添加表格ID
 * @param {string} tableId - 表格ID
 * @returns {boolean} 是否添加成功
 */
export function addTableId(tableId) {
  try {
    if (!tableId) {
      return false
    }
    const ids = getAllTableIds()
    if (ids.includes(tableId)) {
      return false
    }
    ids.push(tableId)
    setStorage(TABLE_IDS_KEY, ids, StorageType.SESSION)
    
    const order = getTableOrder()
    order.push(tableId)
    setStorage(TABLE_ORDER_KEY, order, StorageType.SESSION)
    
    return true
  } catch (error) {
    console.error('Add table ID error:', error)
    return false
  }
}

/**
 * 删除表格ID
 * @param {string} tableId - 表格ID
 * @returns {boolean} 是否删除成功
 */
export function removeTableId(tableId) {
  try {
    if (!tableId) {
      return false
    }
    const ids = getAllTableIds()
    const index = ids.indexOf(tableId)
    if (index === -1) {
      return false
    }
    ids.splice(index, 1)
    setStorage(TABLE_IDS_KEY, ids, StorageType.SESSION)
    
    const order = getTableOrder()
    const orderIndex = order.indexOf(tableId)
    if (orderIndex !== -1) {
      order.splice(orderIndex, 1)
      setStorage(TABLE_ORDER_KEY, order, StorageType.SESSION)
    }
    
    return true
  } catch (error) {
    console.error('Remove table ID error:', error)
    return false
  }
}

/**
 * 调整表格ID顺序
 * @param {Array<string>} orderArray - 顺序数组
 * @returns {boolean} 是否调整成功
 */
export function updateTableOrder(orderArray) {
  try {
    if (!Array.isArray(orderArray)) {
      return false
    }
    const ids = getAllTableIds()
    const validOrder = orderArray.filter(id => ids.includes(id))
    const missingIds = ids.filter(id => !orderArray.includes(id))
    const finalOrder = [...validOrder, ...missingIds]
    setStorage(TABLE_ORDER_KEY, finalOrder, StorageType.SESSION)
    return true
  } catch (error) {
    console.error('Update table order error:', error)
    return false
  }
}

/**
 * 清空所有表格ID
 * @returns {boolean} 是否清空成功
 */
export function clearTableIds() {
  try {
    removeStorage(TABLE_IDS_KEY, StorageType.SESSION)
    removeStorage(TABLE_ORDER_KEY, StorageType.SESSION)
    return true
  } catch (error) {
    console.error('Clear table IDs error:', error)
    return false
  }
}

/**
 * 获取所有表格ID
 * @returns {Array<string>} 表格ID数组
 */
export function getAllTableIds() {
  try {
    return getStorage(TABLE_IDS_KEY, [], StorageType.SESSION)
  } catch (error) {
    console.error('Get all table IDs error:', error)
    return []
  }
}

/**
 * 获取表格ID顺序数组
 * @returns {Array<string>} 顺序数组
 */
export function getTableOrder() {
  try {
    return getStorage(TABLE_ORDER_KEY, [], StorageType.SESSION)
  } catch (error) {
    console.error('Get table order error:', error)
    return []
  }
}
