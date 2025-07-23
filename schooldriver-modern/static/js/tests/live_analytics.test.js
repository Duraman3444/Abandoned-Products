/**
 * Live Analytics Module Tests (Jasmine/Jest compatible)
 */

describe('LiveAnalytics', () => {
    let mockCanvas, mockCtx, liveAnalytics;

    beforeEach(() => {
        // Mock DOM elements
        document.body.innerHTML = `
            <canvas id="testChart" width="400" height="200"></canvas>
            <button id="pauseLiveAnalytics">Pause</button>
        `;

        // Mock Canvas and Chart.js
        mockCtx = {
            canvas: { width: 400, height: 200 },
            clearRect: jasmine.createSpy('clearRect'),
            drawImage: jasmine.createSpy('drawImage'),
            getImageData: jasmine.createSpy('getImageData'),
            putImageData: jasmine.createSpy('putImageData')
        };

        mockCanvas = document.getElementById('testChart');
        spyOn(mockCanvas, 'getContext').and.returnValue(mockCtx);

        // Mock Chart.js
        window.Chart = jasmine.createSpy('Chart').and.callFake(function(ctx, config) {
            this.data = config.data;
            this.options = config.options;
            this.update = jasmine.createSpy('update');
            this.destroy = jasmine.createSpy('destroy');
        });

        // Mock requestAnimationFrame
        spyOn(window, 'requestAnimationFrame').and.callFake((callback) => {
            setTimeout(callback, 16); // ~60fps
            return 1;
        });
        spyOn(window, 'cancelAnimationFrame');

        // Mock performance for timestamp
        if (!window.performance) {
            window.performance = { now: () => Date.now() };
        }
    });

    afterEach(() => {
        if (liveAnalytics) {
            liveAnalytics.destroy();
            liveAnalytics = null;
        }
        jasmine.clock().uninstall();
    });

    describe('Initialization', () => {
        it('should create LiveAnalytics instance with default options', () => {
            liveAnalytics = new LiveAnalytics('testChart');
            
            expect(liveAnalytics).toBeDefined();
            expect(liveAnalytics.maxDataPoints).toBe(50);
            expect(liveAnalytics.updateInterval).toBe(2000);
            expect(liveAnalytics.maxFPS).toBe(30);
        });

        it('should create LiveAnalytics instance with custom options', () => {
            const options = {
                maxDataPoints: 100,
                updateInterval: 1000,
                maxFPS: 60
            };
            
            liveAnalytics = new LiveAnalytics('testChart', options);
            
            expect(liveAnalytics.maxDataPoints).toBe(100);
            expect(liveAnalytics.updateInterval).toBe(1000);
            expect(liveAnalytics.maxFPS).toBe(60);
        });

        it('should initialize Chart.js with correct configuration', () => {
            liveAnalytics = new LiveAnalytics('testChart');
            
            expect(window.Chart).toHaveBeenCalled();
            const chartConfig = window.Chart.calls.mostRecent().args[1];
            
            expect(chartConfig.type).toBe('line');
            expect(chartConfig.data.datasets[0].label).toBe('Live Metrics');
            expect(chartConfig.options.responsive).toBe(true);
        });
    });

    describe('Data Generation and Management', () => {
        beforeEach(() => {
            jasmine.clock().install();
            liveAnalytics = new LiveAnalytics('testChart');
        });

        it('should generate realistic data points', () => {
            const dataPoint = liveAnalytics.generateDataPoint();
            
            expect(typeof dataPoint).toBe('number');
            expect(dataPoint).toBeGreaterThanOrEqual(0);
            expect(dataPoint).toBeLessThanOrEqual(100);
        });

        it('should add data points with proper sliding window', () => {
            // Add 60 data points (more than maxDataPoints of 50)
            for (let i = 0; i < 60; i++) {
                liveAnalytics.addDataPoint();
            }
            
            expect(liveAnalytics.dataPoints.length).toBe(50);
            expect(liveAnalytics.labels.length).toBe(50);
        });

        it('should format timestamps correctly', () => {
            const timestamp = new Date('2023-01-01T12:30:45').getTime();
            const formatted = liveAnalytics.formatTimestamp(timestamp);
            
            expect(formatted).toMatch(/^\d{2}:\d{2}:\d{2}$/);
        });

        it('should fire dataPointAdded event', (done) => {
            let eventFired = false;
            
            mockCanvas.addEventListener('dataPointAdded', (event) => {
                expect(event.detail.value).toBeDefined();
                expect(event.detail.timestamp).toBeDefined();
                expect(event.detail.totalPoints).toBeDefined();
                eventFired = true;
                done();
            });
            
            liveAnalytics.addDataPoint();
            
            setTimeout(() => {
                if (!eventFired) {
                    fail('dataPointAdded event was not fired');
                    done();
                }
            }, 100);
        });
    });

    describe('Real-time Updates', () => {
        beforeEach(() => {
            jasmine.clock().install();
            liveAnalytics = new LiveAnalytics('testChart', { updateInterval: 100 }); // Faster for testing
        });

        it('should add new data points over time', (done) => {
            const initialCount = liveAnalytics.dataPoints.length;
            
            // Wait for at least 5 updates (500ms with 100ms interval)
            setTimeout(() => {
                const finalCount = liveAnalytics.dataPoints.length;
                expect(finalCount).toBeGreaterThan(initialCount);
                expect(finalCount - initialCount).toBeGreaterThanOrEqual(5);
                done();
            }, 550);
            
            jasmine.clock().tick(550);
        });

        it('should update continuously without stopping', (done) => {
            let updateCount = 0;
            const originalAddDataPoint = liveAnalytics.addDataPoint;
            
            spyOn(liveAnalytics, 'addDataPoint').and.callFake(function() {
                updateCount++;
                return originalAddDataPoint.call(this);
            });
            
            // Check that updates continue for at least 10 seconds
            setTimeout(() => {
                expect(updateCount).toBeGreaterThanOrEqual(100); // 10 seconds / 100ms = 100 updates
                done();
            }, 10000);
            
            jasmine.clock().tick(10000);
        });

        it('should maintain exactly 50 data points after initial fill', (done) => {
            // Let it run long enough to exceed 50 points
            setTimeout(() => {
                expect(liveAnalytics.dataPoints.length).toBe(50);
                expect(liveAnalytics.labels.length).toBe(50);
                done();
            }, 6000); // 60 updates = 6 seconds
            
            jasmine.clock().tick(6000);
        });
    });

    describe('Pause and Resume Functionality', () => {
        beforeEach(() => {
            jasmine.clock().install();
            liveAnalytics = new LiveAnalytics('testChart', { updateInterval: 100 });
        });

        it('should pause updates when pause() is called', () => {
            liveAnalytics.pause();
            
            expect(liveAnalytics.paused).toBe(true);
            expect(window.cancelAnimationFrame).toHaveBeenCalled();
        });

        it('should resume updates when resume() is called', () => {
            liveAnalytics.pause();
            liveAnalytics.resume();
            
            expect(liveAnalytics.paused).toBe(false);
            expect(window.requestAnimationFrame).toHaveBeenCalled();
        });

        it('should toggle between pause and resume states', () => {
            const isRunning1 = liveAnalytics.toggle();
            expect(isRunning1).toBe(false); // Should be paused
            expect(liveAnalytics.paused).toBe(true);
            
            const isRunning2 = liveAnalytics.toggle();
            expect(isRunning2).toBe(true); // Should be running
            expect(liveAnalytics.paused).toBe(false);
        });

        it('should not add data points when paused', (done) => {
            const initialCount = liveAnalytics.dataPoints.length;
            
            liveAnalytics.pause();
            
            setTimeout(() => {
                const finalCount = liveAnalytics.dataPoints.length;
                expect(finalCount).toBe(initialCount); // Should not have changed
                done();
            }, 500);
            
            jasmine.clock().tick(500);
        });
    });

    describe('Performance and Frame Rate', () => {
        beforeEach(() => {
            liveAnalytics = new LiveAnalytics('testChart', { maxFPS: 30 });
        });

        it('should limit frame rate to specified FPS', () => {
            expect(liveAnalytics.frameInterval).toBe(1000 / 30); // ~33.33ms
        });

        it('should use requestAnimationFrame for smooth animations', () => {
            liveAnalytics.start();
            
            expect(window.requestAnimationFrame).toHaveBeenCalled();
        });
    });

    describe('Memory Management and Cleanup', () => {
        beforeEach(() => {
            liveAnalytics = new LiveAnalytics('testChart');
        });

        it('should clean up resources when destroyed', () => {
            const chartInstance = liveAnalytics.chart;
            
            liveAnalytics.destroy();
            
            expect(chartInstance.destroy).toHaveBeenCalled();
            expect(liveAnalytics.chart).toBe(null);
            expect(liveAnalytics.updateTimer).toBe(null);
        });

        it('should provide status information', () => {
            const status = liveAnalytics.getStatus();
            
            expect(status.paused).toBeDefined();
            expect(status.dataPoints).toBeDefined();
            expect(status.maxDataPoints).toBeDefined();
            expect(status.updateInterval).toBeDefined();
            expect(status.uptime).toBeDefined();
        });

        it('should provide data for testing', () => {
            liveAnalytics.addDataPoint();
            liveAnalytics.addDataPoint();
            
            const data = liveAnalytics.getData();
            
            expect(data.labels).toEqual(jasmine.any(Array));
            expect(data.data).toEqual(jasmine.any(Array));
            expect(data.labels.length).toBe(data.data.length);
        });
    });

    describe('Integration Functions', () => {
        it('should initialize global instance with initializeLiveAnalytics', () => {
            const instance = initializeLiveAnalytics('testChart');
            
            expect(instance).toBeDefined();
            expect(instance instanceof LiveAnalytics).toBe(true);
            
            // Cleanup
            instance.destroy();
        });

        it('should setup pause button event listener', () => {
            const pauseButton = document.getElementById('pauseLiveAnalytics');
            spyOn(pauseButton, 'addEventListener');
            
            const instance = initializeLiveAnalytics('testChart');
            
            expect(pauseButton.addEventListener).toHaveBeenCalledWith('click', jasmine.any(Function));
            
            // Cleanup
            instance.destroy();
        });
    });
});

// Performance test for continuous updates
describe('LiveAnalytics Performance', () => {
    let liveAnalytics;
    const startTime = performance.now();

    beforeEach(() => {
        document.body.innerHTML = '<canvas id="perfChart"></canvas>';
        
        // Mock Chart.js for performance testing
        window.Chart = function(ctx, config) {
            this.data = config.data;
            this.update = jasmine.createSpy('update');
            this.destroy = jasmine.createSpy('destroy');
        };
    });

    afterEach(() => {
        if (liveAnalytics) {
            liveAnalytics.destroy();
        }
    });

    it('should handle 1000 data point updates without memory leaks', (done) => {
        liveAnalytics = new LiveAnalytics('perfChart', {
            maxDataPoints: 50,
            updateInterval: 1, // Very fast for stress test
            maxFPS: 60
        });

        let updateCount = 0;
        const startMemory = performance.memory ? performance.memory.usedJSHeapSize : 0;

        const checkUpdates = setInterval(() => {
            updateCount++;
            liveAnalytics.addDataPoint();
            
            if (updateCount >= 1000) {
                clearInterval(checkUpdates);
                
                const endTime = performance.now();
                const endMemory = performance.memory ? performance.memory.usedJSHeapSize : 0;
                const memoryIncrease = endMemory - startMemory;
                
                // Should maintain exactly 50 data points
                expect(liveAnalytics.dataPoints.length).toBe(50);
                
                // Memory increase should be reasonable (less than 10MB)
                if (performance.memory) {
                    expect(memoryIncrease).toBeLessThan(10 * 1024 * 1024);
                }
                
                // Should complete in reasonable time (less than 5 seconds)
                expect(endTime - startTime).toBeLessThan(5000);
                
                done();
            }
        }, 1);
    });
});
