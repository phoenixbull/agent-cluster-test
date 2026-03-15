/**
 * 箭头会拐弯 - 微信小程序游戏复刻版
 * v2.0.1 - 修复启动和重生问题
 */

class ArrowGame {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.resize();
        
        // 游戏状态
        this.state = 'start';
        this.score = 0;
        this.combo = 0;
        this.maxCombo = 0;
        this.currentLevel = 1;
        this.lives = 3;
        
        // 箭头属性
        this.arrow = {
            x: this.width / 2,
            y: this.height - 100,
            direction: 0,
            speed: 150,
            length: 30,
            width: 8,
            color: '#FF6B6B',
            trail: []
        };
        
        // 游戏对象
        this.obstacles = [];
        this.checkpoints = [];
        this.particles = [];
        this.floatingTexts = [];
        
        // 关卡系统
        this.totalLevels = 20;
        this.levels = this.loadLevels();
        
        // 输入处理
        this.setupInput();
        
        // 音频
        this.audio = this.initAudio();
        
        // 游戏循环
        this.lastTime = 0;
        this.gameLoop = this.gameLoop.bind(this);
        requestAnimationFrame(this.gameLoop);
    }
    
    resize() {
        this.width = window.innerWidth;
        this.height = window.innerHeight;
        this.canvas.width = this.width;
        this.canvas.height = this.height;
    }
    
    initAudio() {
        return {
            play: (type) => {
                try {
                    const AudioContext = window.AudioContext || window.webkitAudioContext;
                    if (!AudioContext) return;
                    
                    const ctx = new AudioContext();
                    const osc = ctx.createOscillator();
                    const gain = ctx.createGain();
                    
                    osc.connect(gain);
                    gain.connect(ctx.destination);
                    
                    switch(type) {
                        case 'turn':
                            osc.frequency.value = 800;
                            gain.gain.setValueAtTime(0.3, ctx.currentTime);
                            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.1);
                            osc.start(ctx.currentTime);
                            osc.stop(ctx.currentTime + 0.1);
                            break;
                        case 'score':
                            osc.frequency.value = 1200;
                            gain.gain.setValueAtTime(0.3, ctx.currentTime);
                            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.2);
                            osc.start(ctx.currentTime);
                            osc.stop(ctx.currentTime + 0.2);
                            break;
                        case 'collision':
                            osc.type = 'sawtooth';
                            osc.frequency.value = 200;
                            gain.gain.setValueAtTime(0.5, ctx.currentTime);
                            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);
                            osc.start(ctx.currentTime);
                            osc.stop(ctx.currentTime + 0.3);
                            break;
                        case 'levelup':
                            osc.frequency.value = 600;
                            gain.gain.setValueAtTime(0.3, ctx.currentTime);
                            osc.frequency.linearRampToValueAtTime(1200, ctx.currentTime + 0.3);
                            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.5);
                            osc.start(ctx.currentTime);
                            osc.stop(ctx.currentTime + 0.5);
                            break;
                    }
                } catch(e) {
                    console.log('Audio error:', e);
                }
            }
        };
    }
    
    setupInput() {
        const turnHandler = (e) => {
            e.preventDefault();
            
            if (this.state === 'start') {
                this.startGame();
            } else if (this.state === 'gameover') {
                this.startGame();
            } else if (this.state === 'levelcomplete') {
                this.nextLevel();
            } else if (this.state === 'playing') {
                this.turnArrow();
            }
        };
        
        this.canvas.addEventListener('touchstart', turnHandler, { passive: false });
        this.canvas.addEventListener('mousedown', turnHandler);
        
        this.canvas.addEventListener('keydown', (e) => {
            if (e.code === 'Space') {
                e.preventDefault();
                if (this.state === 'start' || this.state === 'gameover') {
                    this.startGame();
                } else if (this.state === 'levelcomplete') {
                    this.nextLevel();
                } else if (this.state === 'playing') {
                    this.turnArrow();
                }
            }
        });
        
        window.addEventListener('resize', () => this.resize());
    }
    
    turnArrow() {
        this.arrow.direction = (this.arrow.direction + 1) % 4;
        this.combo++;
        if (this.combo > this.maxCombo) {
            this.maxCombo = this.combo;
        }
        
        this.audio.play('turn');
        this.createParticles(this.arrow.x, this.arrow.y, 5, '#FFD93D');
        
        if (this.combo > 1) {
            this.showFloatingText(`${this.combo}连击!`, this.arrow.x, this.arrow.y - 30, '#FFD93D');
        }
    }
    
    createParticles(x, y, count, color) {
        for (let i = 0; i < count; i++) {
            this.particles.push({
                x, y,
                vx: (Math.random() - 0.5) * 100,
                vy: (Math.random() - 0.5) * 100,
                life: 1.0,
                color
            });
        }
    }
    
    showFloatingText(text, x, y, color) {
        this.floatingTexts.push({
            text, x, y,
            life: 1.5,
            color,
            vy: -50
        });
    }
    
    loadLevels() {
        const levels = [];
        
        for (let i = 1; i <= this.totalLevels; i++) {
            const level = {
                level: i,
                obstacles: [],
                checkpoints: [],
                targetScore: i * 50,
                speed: 150 + i * 10,
                themeColor: this.getLevelTheme(i)
            };
            
            // 简化障碍物配置，确保不会立即碰撞
            if (i <= 3) {
                // 教学关：障碍物远离起点
                level.obstacles = [
                    { x: this.width * 0.7, y: this.height * 0.1, width: 20, height: this.height * 0.3 },
                    { x: this.width * 0.2, y: this.height * 0.4, width: this.width * 0.3, height: 20 }
                ];
            } else if (i <= 8) {
                level.obstacles = [
                    { x: this.width * 0.1, y: this.height * 0.1, width: 20, height: this.height * 0.3 },
                    { x: this.width * 0.4, y: this.height * 0.3, width: this.width * 0.3, height: 20 },
                    { x: this.width * 0.7, y: this.height * 0.5, width: 20, height: this.height * 0.3 }
                ];
            } else {
                // 更多障碍物
                for (let j = 0; j < Math.min(i, 8); j++) {
                    level.obstacles.push({
                        x: this.width * (0.1 + (j % 4) * 0.25),
                        y: this.height * (0.1 + Math.floor(j / 4) * 0.4),
                        width: j % 2 === 0 ? 20 : this.width * 0.2,
                        height: j % 2 === 0 ? this.height * 0.3 : 20
                    });
                }
            }
            
            level.checkpoints = [
                { x: this.width * 0.3, y: this.height * 0.3, radius: 30, collected: false },
                { x: this.width * 0.7, y: this.height * 0.6, radius: 30, collected: false }
            ];
            
            levels.push(level);
        }
        
        return levels;
    }
    
    getLevelTheme(level) {
        const themes = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
            '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
            '#F8B500', '#FF6F61', '#6B5B95', '#88B04B', '#F7CAC9',
            '#92A8D1', '#955251', '#B565A7', '#009B77', '#DD4124'
        ];
        return themes[(level - 1) % themes.length];
    }
    
    startGame() {
        console.log('Starting game...');
        this.state = 'playing';
        this.score = 0;
        this.combo = 0;
        this.lives = 3;
        this.currentLevel = 1;
        this.resetArrow();
        this.loadLevel(1);
        this.audio.play('levelup');
        console.log('Game started! State:', this.state);
    }
    
    nextLevel() {
        this.currentLevel++;
        if (this.currentLevel > this.totalLevels) {
            this.currentLevel = 1;
        }
        this.loadLevel(this.currentLevel);
        this.audio.play('levelup');
    }
    
    loadLevel(levelNum) {
        const level = this.levels[levelNum - 1];
        if (level) {
            this.obstacles = JSON.parse(JSON.stringify(level.obstacles));
            this.checkpoints = JSON.parse(JSON.stringify(level.checkpoints));
            this.resetArrow();
        }
    }
    
    resetArrow() {
        // 确保箭头出生在安全位置（屏幕底部中间）
        this.arrow.x = this.width / 2;
        this.arrow.y = this.height - 150;
        this.arrow.direction = 0;
        this.arrow.trail = [];
        this.combo = 0;
        console.log('Arrow reset to:', this.arrow.x, this.arrow.y);
    }
    
    update(deltaTime) {
        if (this.state !== 'playing') return;
        if (deltaTime > 0.1) return; // 防止切换标签页后的巨大 deltaTime
        
        const moveDistance = this.arrow.speed * deltaTime;
        const oldX = this.arrow.x;
        const oldY = this.arrow.y;
        
        switch (this.arrow.direction) {
            case 0: this.arrow.y -= moveDistance; break;
            case 1: this.arrow.x += moveDistance; break;
            case 2: this.arrow.y += moveDistance; break;
            case 3: this.arrow.x -= moveDistance; break;
        }
        
        // 添加拖尾
        this.arrow.trail.push({ x: oldX, y: oldY, life: 1.0 });
        if (this.arrow.trail.length > 20) {
            this.arrow.trail.shift();
        }
        this.arrow.trail.forEach(t => t.life -= deltaTime * 2);
        this.arrow.trail = this.arrow.trail.filter(t => t.life > 0);
        
        // 边界检测 - 只检测是否超出边界，不立即死亡
        if (this.checkBoundaryCollision()) {
            this.handleCollision('boundary');
            return;
        }
        
        // 障碍物检测
        if (this.checkObstacleCollision()) {
            this.handleCollision('obstacle');
            return;
        }
        
        // 检查点检测
        this.checkpoints.forEach(cp => {
            if (!cp.collected) {
                const dx = this.arrow.x - cp.x;
                const dy = this.arrow.y - cp.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < cp.radius + 10) {
                    cp.collected = true;
                    this.score += 100;
                    this.audio.play('score');
                    this.showFloatingText('+100', cp.x, cp.y, '#4ECDC4');
                    this.createParticles(cp.x, cp.y, 10, '#4ECDC4');
                }
            }
        });
        
        // 持续得分
        this.score += Math.floor(moveDistance);
        
        // 更新粒子
        this.particles.forEach(p => {
            p.x += p.vx * deltaTime;
            p.y += p.vy * deltaTime;
            p.life -= deltaTime * 2;
        });
        this.particles = this.particles.filter(p => p.life > 0);
        
        // 更新浮动文字
        this.floatingTexts.forEach(t => {
            t.y += t.vy * deltaTime;
            t.life -= deltaTime;
        });
        this.floatingTexts = this.floatingTexts.filter(t => t.life > 0);
        
        // 检查关卡完成
        if (this.score >= this.levels[this.currentLevel - 1].targetScore) {
            this.state = 'levelcomplete';
        }
    }
    
    checkBoundaryCollision() {
        // 箭头稍微超出边界才判定碰撞
        const margin = 20;
        return (this.arrow.x < -margin || 
                this.arrow.x > this.width + margin ||
                this.arrow.y < -margin || 
                this.arrow.y > this.height + margin);
    }
    
    checkObstacleCollision() {
        const arrowSize = 15; // 箭头碰撞盒大小
        
        for (const obs of this.obstacles) {
            if (this.arrow.x > obs.x - arrowSize && 
                this.arrow.x < obs.x + obs.width + arrowSize &&
                this.arrow.y > obs.y - arrowSize && 
                this.arrow.y < obs.y + obs.height + arrowSize) {
                return true;
            }
        }
        return false;
    }
    
    handleCollision(type) {
        console.log('Collision:', type, 'Lives:', this.lives);
        this.lives--;
        this.combo = 0;
        this.audio.play('collision');
        this.createParticles(this.arrow.x, this.arrow.y, 20, '#FF0000');
        
        if (this.lives <= 0) {
            console.log('Game Over!');
            this.state = 'gameover';
        } else {
            // 重置箭头位置到安全点
            this.resetArrow();
            this.showFloatingText(`生命 -1`, this.width / 2, this.height / 2, '#FF0000');
        }
    }
    
    draw() {
        const gradient = this.ctx.createLinearGradient(0, 0, 0, this.height);
        gradient.addColorStop(0, '#1a1a2e');
        gradient.addColorStop(1, '#16213e');
        this.ctx.fillStyle = gradient;
        this.ctx.fillRect(0, 0, this.width, this.height);
        
        if (this.state === 'start') {
            this.drawStartScreen();
        } else if (this.state === 'playing') {
            this.drawGame();
        } else if (this.state === 'gameover') {
            this.drawGame();
            this.drawGameOver();
        } else if (this.state === 'levelcomplete') {
            this.drawGame();
            this.drawLevelComplete();
        }
    }
    
    drawArrow() {
        this.ctx.save();
        this.ctx.translate(this.arrow.x, this.arrow.y);
        this.ctx.rotate(this.arrow.direction * Math.PI / 2);
        
        // 绘制拖尾
        this.arrow.trail.forEach((t, i) => {
            const alpha = t.life * 0.5;
            this.ctx.fillStyle = `rgba(255, 107, 107, ${alpha})`;
            const size = (i / this.arrow.trail.length) * this.arrow.width;
            this.ctx.beginPath();
            this.ctx.arc(t.x - this.arrow.x, t.y - this.arrow.y, size, 0, Math.PI * 2);
            this.ctx.fill();
        });
        
        // 绘制箭头
        this.ctx.fillStyle = this.arrow.color;
        this.ctx.shadowColor = this.arrow.color;
        this.ctx.shadowBlur = 15;
        
        this.ctx.beginPath();
        this.ctx.moveTo(0, -this.arrow.length);
        this.ctx.lineTo(-this.arrow.width, this.arrow.width);
        this.ctx.lineTo(0, this.arrow.width / 2);
        this.ctx.lineTo(this.arrow.width, this.arrow.width);
        this.ctx.closePath();
        this.ctx.fill();
        
        this.ctx.restore();
        this.ctx.shadowBlur = 0;
    }
    
    drawObstacles() {
        this.ctx.fillStyle = '#E94560';
        this.ctx.shadowColor = '#E94560';
        this.ctx.shadowBlur = 10;
        
        for (const obs of this.obstacles) {
            this.ctx.fillRect(obs.x, obs.y, obs.width, obs.height);
        }
        
        this.ctx.shadowBlur = 0;
    }
    
    drawCheckpoints() {
        for (const cp of this.checkpoints) {
            if (!cp.collected) {
                this.ctx.beginPath();
                this.ctx.arc(cp.x, cp.y, cp.radius, 0, Math.PI * 2);
                this.ctx.fillStyle = 'rgba(78, 205, 196, 0.3)';
                this.ctx.fill();
                this.ctx.lineWidth = 3;
                this.ctx.strokeStyle = '#4ECDC4';
                this.ctx.stroke();
                
                this.ctx.shadowColor = '#4ECDC4';
                this.ctx.shadowBlur = 20;
                this.ctx.stroke();
                this.ctx.shadowBlur = 0;
            }
        }
    }
    
    drawParticles() {
        this.particles.forEach(p => {
            this.ctx.globalAlpha = p.life;
            this.ctx.fillStyle = p.color;
            this.ctx.beginPath();
            this.ctx.arc(p.x, p.y, 5 * p.life, 0, Math.PI * 2);
            this.ctx.fill();
        });
        this.ctx.globalAlpha = 1.0;
    }
    
    drawFloatingTexts() {
        this.floatingTexts.forEach(t => {
            this.ctx.globalAlpha = t.life;
            this.ctx.fillStyle = t.color;
            this.ctx.font = 'bold 24px Arial';
            this.ctx.fillText(t.text, t.x, t.y);
        });
        this.ctx.globalAlpha = 1.0;
    }
    
    drawUI() {
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.font = 'bold 24px Arial';
        this.ctx.textAlign = 'left';
        this.ctx.fillText(`分数：${this.score}`, 20, 40);
        
        if (this.combo > 1) {
            this.ctx.fillStyle = '#FFD93D';
            this.ctx.font = 'bold 20px Arial';
            this.ctx.fillText(`连击：${this.combo}x`, 20, 70);
        }
        
        this.ctx.fillStyle = '#FF6B6B';
        this.ctx.font = 'bold 20px Arial';
        this.ctx.fillText(`生命：${'❤️'.repeat(this.lives)}`, 20, 100);
        
        this.ctx.fillStyle = '#4ECDC4';
        this.ctx.font = 'bold 20px Arial';
        this.ctx.fillText(`关卡：${this.currentLevel}/${this.totalLevels}`, 20, 130);
        
        const targetScore = this.levels[this.currentLevel - 1]?.targetScore || 0;
        this.ctx.fillStyle = '#95A5A6';
        this.ctx.font = '16px Arial';
        this.ctx.fillText(`目标：${targetScore}`, 20, 155);
    }
    
    drawStartScreen() {
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.textAlign = 'center';
        
        this.ctx.font = 'bold 48px Arial';
        this.ctx.shadowColor = '#FF6B6B';
        this.ctx.shadowBlur = 20;
        this.ctx.fillText('箭头会拐弯', this.width / 2, this.height / 2 - 100);
        this.ctx.shadowBlur = 0;
        
        this.ctx.font = '20px Arial';
        this.ctx.fillStyle = '#BDC3C7';
        this.ctx.fillText('点击屏幕或按空格键使箭头 90 度转向', this.width / 2, this.height / 2 - 20);
        this.ctx.fillText('避开障碍物，收集检查点', this.width / 2, this.height / 2 + 20);
        this.ctx.fillText('达到目标分数进入下一关', this.width / 2, this.height / 2 + 60);
        
        const btnWidth = 200;
        const btnHeight = 60;
        const btnX = this.width / 2 - btnWidth / 2;
        const btnY = this.height / 2 + 100;
        
        this.ctx.fillStyle = '#FF6B6B';
        this.ctx.shadowColor = '#FF6B6B';
        this.ctx.shadowBlur = 15;
        if (this.ctx.roundRect) {
            this.ctx.roundRect(btnX, btnY, btnWidth, btnHeight, 10);
        } else {
            this.ctx.fillRect(btnX, btnY, btnWidth, btnHeight);
        }
        this.ctx.fill();
        this.ctx.shadowBlur = 0;
        
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.font = 'bold 24px Arial';
        this.ctx.fillText('开始游戏', this.width / 2, btnY + 38);
    }
    
    drawGameOver() {
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        this.ctx.fillRect(0, 0, this.width, this.height);
        
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.textAlign = 'center';
        
        this.ctx.font = 'bold 48px Arial';
        this.ctx.shadowColor = '#E94560';
        this.ctx.shadowBlur = 20;
        this.ctx.fillText('游戏结束', this.width / 2, this.height / 2 - 80);
        this.ctx.shadowBlur = 0;
        
        this.ctx.font = '28px Arial';
        this.ctx.fillStyle = '#FFD93D';
        this.ctx.fillText(`最终分数：${this.score}`, this.width / 2, this.height / 2);
        
        this.ctx.fillStyle = '#4ECDC4';
        this.ctx.fillText(`最大连击：${this.maxCombo}x`, this.width / 2, this.height / 2 + 50);
        
        this.ctx.fillStyle = '#95A5A6';
        this.ctx.fillText(`到达关卡：${this.currentLevel}`, this.width / 2, this.height / 2 + 90);
        
        const btnWidth = 200;
        const btnHeight = 60;
        const btnX = this.width / 2 - btnWidth / 2;
        const btnY = this.height / 2 + 130;
        
        this.ctx.fillStyle = '#FF6B6B';
        this.ctx.shadowColor = '#FF6B6B';
        this.ctx.shadowBlur = 15;
        if (this.ctx.roundRect) {
            this.ctx.roundRect(btnX, btnY, btnWidth, btnHeight, 10);
        } else {
            this.ctx.fillRect(btnX, btnY, btnWidth, btnHeight);
        }
        this.ctx.fill();
        this.ctx.shadowBlur = 0;
        
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.font = 'bold 24px Arial';
        this.ctx.fillText('重新开始', this.width / 2, btnY + 38);
    }
    
    drawLevelComplete() {
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
        this.ctx.fillRect(0, 0, this.width, this.height);
        
        this.ctx.fillStyle = '#4ECDC4';
        this.ctx.textAlign = 'center';
        this.ctx.font = 'bold 48px Arial';
        this.ctx.shadowColor = '#4ECDC4';
        this.ctx.shadowBlur = 20;
        this.ctx.fillText('关卡完成!', this.width / 2, this.height / 2 - 50);
        this.ctx.shadowBlur = 0;
        
        this.ctx.font = '28px Arial';
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.fillText(`分数：${this.score}`, this.width / 2, this.height / 2 + 20);
        
        const btnWidth = 200;
        const btnHeight = 60;
        const btnX = this.width / 2 - btnWidth / 2;
        const btnY = this.height / 2 + 80;
        
        this.ctx.fillStyle = '#4ECDC4';
        this.ctx.shadowColor = '#4ECDC4';
        this.ctx.shadowBlur = 15;
        if (this.ctx.roundRect) {
            this.ctx.roundRect(btnX, btnY, btnWidth, btnHeight, 10);
        } else {
            this.ctx.fillRect(btnX, btnY, btnWidth, btnHeight);
        }
        this.ctx.fill();
        this.ctx.shadowBlur = 0;
        
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.font = 'bold 24px Arial';
        this.ctx.fillText('下一关', this.width / 2, btnY + 38);
    }
    
    drawGame() {
        this.drawCheckpoints();
        this.drawObstacles();
        this.drawArrow();
        this.drawParticles();
        this.drawFloatingTexts();
        this.drawUI();
    }
    
    gameLoop(timestamp) {
        const deltaTime = (timestamp - this.lastTime) / 1000;
        this.lastTime = timestamp;
        
        this.update(deltaTime);
        this.draw();
        
        requestAnimationFrame(this.gameLoop);
    }
}

// 初始化游戏
window.addEventListener('load', () => {
    const canvas = document.getElementById('gameCanvas');
    if (canvas) {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        const game = new ArrowGame(canvas);
        console.log('Game initialized!');
    }
});
