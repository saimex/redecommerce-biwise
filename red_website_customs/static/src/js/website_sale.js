/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import publicWidget from "@web/legacy/js/public/public_widget";
import { debounce, throttleForAnimation } from "@web/core/utils/timing";

publicWidget.registry.WebsiteSale.include({
    events: Object.assign({}, publicWidget.registry.WebsiteSale.prototype.events || {}, {
        'change select[name="state_id"]': '_onChangeState',
        'change select[name="county_id"]': '_onChangeCounty',
    }),
    init: function () {
        this._super.apply(this, arguments);
        this._changeState = debounce(this._changeState.bind(this), 500);
        this._changeCounty = debounce(this._changeCounty.bind(this), 500);
    },
    _onChangeState: function (ev) {
        console.log('---------CHECKOUT AUTOFORMAT-----------')
        if (!this.$('.checkout_autoformat').length) {
            return;
        }
        return this._changeState();
    },
    _onChangeCounty: function (ev) {
        console.log('---------CHECKOUT AUTOFORMAT-----------')
        if (!this.$('.checkout_autoformat').length) {
            return;
        }
        return this._changeCounty();
    },
    /**
     * @private
     */
    _changeState: function () {
        console.log('---------CHANGE STATE-----------')
        if (!$("#state_id").val()) {
            return;
        }
        return this.rpc("/shop/state_infos/" + $("#state_id").val(), {}).then(function (data) {
            // populate Counties and display
            var selectCounties = $("select[name='county_id']");
            // dont reload state at first loading (done in qweb)
            if (selectCounties.data('init')===0 || selectCounties.find('option').length===1) {
                selectCounties.html('');
                selectCounties.append(_t('<option value="">Select a County...</option>'))
                data.counties.forEach((x) => {
                var opt = $('<option>').text(x[1])
                        .attr('value', x[0])
                        .attr('data-code', x[2]);
                    selectCounties.append(opt);
                });
                selectCounties.data('init', 0);
            } else {
                selectCounties.data('init', 0);
            }
        });
    },
    /**
     * @private
     */
    _changeCounty: function () {
        if (!$("#state_id").val()) {
            return;
        }
        return this.rpc("/shop/county_infos/" + $("#county_id").val(), {}).then(function (data) {
            // populate Counties and display
            var selectDistricts = $("select[name='district_id']");
            // dont reload state at first loading (done in qweb)
            if (selectDistricts.data('init')===0 || selectDistricts.find('option').length===1) {
                selectDistricts.html('');
                selectDistricts.append(_t('<option value="">Select a District...</option>'))
                data.districts.forEach((x) => {
                var opt = $('<option>').text(x[1])
                        .attr('value', x[0])
                        .attr('data-code', x[2]);
                    selectDistricts.append(opt);
                });
                selectDistricts.data('init', 0);
            } else {
                selectDistricts.data('init', 0);
            }
        });
    },
});