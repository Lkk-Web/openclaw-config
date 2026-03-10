const Calculator = require('./calculator');

describe('Calculator', () => {
  let calc;

  beforeEach(() => {
    calc = new Calculator();
  });

  test('加法运算', () => {
    expect(calc.add(2, 3)).toBe(5);
  });

  test('减法运算', () => {
    expect(calc.subtract(5, 3)).toBe(2);
  });

  test('乘法运算', () => {
    expect(calc.multiply(4, 3)).toBe(12);
  });

  test('除法运算', () => {
    expect(calc.divide(10, 2)).toBe(5);
  });

  test('除以零抛出错误', () => {
    expect(() => calc.divide(10, 0)).toThrow('除数不能为零');
  });
});
