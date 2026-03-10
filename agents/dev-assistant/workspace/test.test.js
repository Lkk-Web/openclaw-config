// 测试文件 for test.js
const { add, multiply } = require('./test');

console.log('Running tests...\n');

// 测试 add 函数
console.log('Test 1: add(2, 3) = 5');
const result1 = add(2, 3);
console.assert(result1 === 5, `Expected 5, got ${result1}`);
console.log('✓ Passed\n');

// 测试 multiply 函数
console.log('Test 2: multiply(4, 5) = 20');
const result2 = multiply(4, 5);
console.assert(result2 === 20, `Expected 20, got ${result2}`);
console.log('✓ Passed\n');

console.log('All tests passed! ✓');
