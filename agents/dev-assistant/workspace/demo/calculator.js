// 简单的计算器模块
class Calculator {
  add(a, b) {
    return a + b;
  }

  subtract(a, b) {
    return a - b;
  }

  multiply(a, b) {
    return a * b;
  }

  divide(a, b) {
    if (b === 0) {
      throw new Error('除数不能为零');
    }
    return a / b;
  }
}

module.exports = Calculator;
